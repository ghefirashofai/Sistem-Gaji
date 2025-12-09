# app.py
import streamlit as st
import json, os
import pandas as pd
from datetime import date, datetime
import altair as alt
from calendar import monthrange

# ---------------------
# Config / DB filename
# ---------------------
DB_FILE = "databaseghe1.json"

# ---------------------
# Utility: load/save DB
# ---------------------
def load_db():
    if not os.path.exists(DB_FILE):
        # default structure
        return {
            "karyawan": {},    # name -> {password, posisi, weeks? (optional), absen: { 'YYYY-MM-DD': {status, overtime}}}
            "pemasukan": {},   # 'YYYY-MM' -> int
            "rates": {         # default rates
                "normal": {"intern":35000,"staff":50000,"spv":100000,"manager":200000},
                "overtime": {"intern":20000,"staff":40000,"spv":55000,"manager":65000}
            }
        }
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

db = load_db()

# ---------------------
# Salary calculation
# ---------------------
def calc_month_salary(name, ym):  # ym = 'YYYY-MM'
    """
    iterate attendance entries for that month and compute:
    hadir = 8h * normal_rate
    hadir+lembur = 8h*normal + overtime_hours*overtime_rate
    izin/sakit/cuti = 0
    return total_amount, detail_rows(list of tuples)
    """
    if name not in db["karyawan"]:
        return 0, []
    pos = db["karyawan"][name]["posisi"]
    normal_rate = db["rates"]["normal"].get(pos, 0)
    ot_rate = db["rates"]["overtime"].get(pos, 0)
    total = 0
    rows = []
    # iterate absen keys
    absen = db["karyawan"][name].get("absen", {})
    for dstr, info in absen.items():
        if dstr.startswith(ym):
            status = info.get("status","")
            overtime = int(info.get("overtime",0))
            if status == "hadir":
                amt = 8 * normal_rate
                total += amt
                rows.append({"date": dstr, "status": status, "overtime": 0, "amount": amt})
            elif status == "hadir+lembur":
                amt = 8 * normal_rate + overtime * ot_rate
                total += amt
                rows.append({"date": dstr, "status": status, "overtime": overtime, "amount": amt})
            else: # izin/sakit/cuti
                rows.append({"date": dstr, "status": status, "overtime": 0, "amount": 0})
    return int(total), rows

# ---------------------
# Helper: format Rupiah
# ---------------------
def rp(x):
    try:
        return f"Rp {int(x):,}"
    except:
        return f"Rp {x}"

# ---------------------
# Auth (karyawan & bendahara)
# ---------------------
BEND_EMAIL = "bendahara@email.com"
BEND_PW = "12345"

def bendahara_login_form():
    st.subheader("Login Bendahara")
    email = st.text_input("Email", key="bend_email")
    pw = st.text_input("Password", type="password", key="bend_pw")
    if st.button("Login Bendahara"):
        if email.strip().lower() == BEND_EMAIL and pw == BEND_PW:
            st.session_state["bendahara"] = True
            st.success("Login berhasil (bendahara).")
            st.experimental_rerun()
        else:
            st.error("Email atau password bendahara salah.")

def karyawan_register():
    st.subheader("Daftar Karyawan")
    col1, col2 = st.columns(2)
    with col1:
        nama = st.text_input("Nama (unique)", key="reg_nama")
    with col2:
        pw = st.text_input("Password", type="password", key="reg_pw")
    posisi = st.selectbox("Posisi", ["intern","staff","spv","manager"], key="reg_pos")
    if st.button("Daftar"):
        if not nama or not pw:
            st.warning("Isi nama dan password.")
        else:
            key = nama.strip().lower()
            if key in db["karyawan"]:
                st.error("Nama sudah terdaftar, gunakan nama lain atau login.")
            else:
                db["karyawan"][key] = {"password": pw, "posisi": posisi, "absen": {}}
                save_db(db)
                st.success("Pendaftaran berhasil. Silakan login di panel Karyawan.")

def karyawan_login():
    st.subheader("Login Karyawan")
    nama = st.text_input("Nama", key="login_nama")
    pw = st.text_input("Password", type="password", key="login_pw")
    if st.button("Login Karyawan"):
        key = nama.strip().lower()
        if key in db["karyawan"] and db["karyawan"][key].get("password") == pw:
            st.session_state["karyawan"] = key
            st.success(f"Login berhasil: {key.title()}")
            st.experimental_rerun()
        else:
            st.error("Nama atau password salah.")

# ---------------------
# UI: Sidebar navigation
# ---------------------
st.set_page_config(page_title="Sistem Gaji (HR)", layout="wide")
st.title("💼 Sistem Gaji & Absensi — Dashboard")

menu = st.sidebar.selectbox("Menu Utama", ["Beranda","Bendahara","Karyawan","Keluar"])
st.sidebar.markdown("---")
# quick info
st.sidebar.write(f"Total karyawan: {len(db['karyawan'])}")

# ---------------------
# BERANDA
# ---------------------
if menu == "Beranda":
    st.header("Ringkasan Singkat")
    total_k = len(db["karyawan"])
    # compute last month payroll sample
    today = date.today()
    cur_ym = today.strftime("%Y-%m")
    total_payroll = 0
    for name in db["karyawan"].keys():
        #s, _ = calc_month_salary := None, None  # placeholder to satisfy editors; we will compute below

    # compute payroll for current month
    total_payroll = sum(calc_month_salary(name, cur_ym)[0] for name in db["karyawan"].keys())
    total_pemasukan = db.get("pemasukan", {}).get(cur_ym, 0)
    col1, col2, col3 = st.columns(3)
    col1.metric("Jumlah Karyawan", total_k)
    col2.metric("Total Payroll (Bulan ini)", rp(total_payroll))
    col3.metric("Pemasukan (Bulan ini)", rp(total_pemasukan))
    st.markdown("---")
    st.write("Gunakan menu **Bendahara** untuk analisa & input pemasukan. Gunakan menu **Karyawan** untuk absen & cek gaji.")

# ---------------------
# BENDARAHA
# ---------------------
elif menu == "Bendahara":
    st.header("🔐 Bendahara — Admin Panel")
    if "bendahara" not in st.session_state or not st.session_state["bendahara"]:
        bendahara_login_form()
        st.stop()

    # authenticated
    st.success("Akses Bendahara aktif.")
    action = st.selectbox("Pilih Aksi", [
        "Dashboard Evaluasi Bulanan",
        "Input Data Karyawan",
        "Lihat Database",
        "Edit Karyawan",
        "Hapus Karyawan",
        "Input Pemasukan Bulanan",
        "Edit Tarif Gaji per Posisi",
        "Logout Bendahara"
    ])

    # ----------------- Dashboard Evaluasi Bulanan -----------------
    if action == "Dashboard Evaluasi Bulanan":
        st.subheader("📊 Dashboard Evaluasi Bulanan")
        # choose month-year
        ym = st.date_input("Pilih bulan (pilih tanggal dalam bulan yang diinginkan):", value=date.today())
        ym_str = ym.strftime("%Y-%m")
        st.write(f"Menampilkan data untuk: **{ym_str}**")
        # total pengeluaran gaji per bulan: sum of calc_month_salary
        rows = []
        for name in db["karyawan"].keys():
            total, details = calc_month_salary(name, ym_str)
            rows.append({"nama": name.title(), "posisi": db["karyawan"][name]["posisi"], "gaji": total})
        df = pd.DataFrame(rows)
        if df.empty:
            st.info("Belum ada data gaji untuk bulan ini.")
        else:
            df = df.sort_values("gaji", ascending=False)
            df["gaji_fmt"] = df["gaji"].map(lambda x: f"{int(x):,}")
            st.markdown("**Tabel Gaji Karyawan (bulan)**")
            st.dataframe(df[["nama","posisi","gaji_fmt"]].rename(columns={"nama":"Nama","posisi":"Posisi","gaji_fmt":"Gaji (Rp)"}), use_container_width=True)

            total_pengeluaran = int(df["gaji"].sum())
            st.metric("Total Pengeluaran Gaji (bulan)", rp(total_pengeluaran))
            # pemasukan bulan
            pemasukan_val = db.get("pemasukan", {}).get(ym_str, 0)
            st.metric("Pemasukan (bulan)", rp(pemasukan_val))
            # pengeluaran per tahun (sum months for that year)
            year = ym.strftime("%Y")
            total_pengeluaran_year = 0
            for m in range(1,13):
                ym2 = f"{year}-{m:02d}"
                total_pengeluaran_year += sum(calc_month_salary(name, ym2)[0] for name in db["karyawan"].keys())
            st.metric("Total Pengeluaran (tahun)", rp(total_pengeluaran_year))

            # attendance performance: compute % hadir (hadir + hadir+lembur considered hadir) over total working days recorded
            perf_rows = []
            for name in db["karyawan"].keys():
                absen = db["karyawan"][name].get("absen", {})
                total_days = sum(1 for d in absen.keys() if d.startswith(ym_str))
                hadir_days = sum(1 for d,v in absen.items() if d.startswith(ym_str) and v.get("status") in ["hadir","hadir+lembur"])
                perf_rows.append({"nama": name.title(), "hadir": hadir_days, "recorded_days": total_days, "attendance_rate": (hadir_days/total_days*100) if total_days>0 else None})
            perf_df = pd.DataFrame(perf_rows)
            if not perf_df.empty:
                perf_df = perf_df.sort_values("attendance_rate", na_position="last", ascending=False)
                st.markdown("**Kinerja Kehadiran Karyawan (%)**")
                st.table(perf_df[["nama","hadir","recorded_days","attendance_rate"]].rename(columns={"nama":"Nama","hadir":"Hadir","recorded_days":"Hari Tercatat","attendance_rate":"% Kehadiran"}).fillna("-"))
                # chart: top 10 attendance
                chart_df = perf_df.dropna(subset=["attendance_rate"])
                if not chart_df.empty:
                    chart = alt.Chart(chart_df.reset_index()).mark_bar().encode(
                        x=alt.X("attendance_rate:Q", title="% Kehadiran"),
                        y=alt.Y("nama:N", sort='-x', title="Karyawan")
                    )
                    st.altair_chart(chart, use_container_width=True)

            # ringkasan lembur
            st.markdown("**Ringkasan Lembur (total jam per karyawan bulan ini)**")
            ot_rows = []
            for name in db["karyawan"].keys():
                absen = db["karyawan"][name].get("absen", {})
                total_ot = sum(int(v.get("overtime",0)) for d,v in absen.items() if d.startswith(ym_str))
                if total_ot>0:
                    ot_rows.append({"nama":name.title(),"total_overtime": total_ot})
            ot_df = pd.DataFrame(ot_rows)
            if not ot_df.empty:
                st.table(ot_df.sort_values("total_overtime", ascending=False).rename(columns={"nama":"Nama","total_overtime":"Jam Lembur"}))
            else:
                st.info("Belum ada data lembur untuk bulan ini.")

    # ----------------- Input Data Karyawan -----------------
    elif action == "Input Data Karyawan":
        st.subheader("➕ Input Data Karyawan")
        with st.form("input_karyawan"):
            nama = st.text_input("Nama (unique)").strip().lower()
            pw = st.text_input("Password (untuk karyawan)", type="password")
            posisi = st.selectbox("Posisi", ["intern","staff","spv","manager"])
            submitted = st.form_submit_button("Simpan")
            if submitted:
                if not nama or not pw:
                    st.warning("Nama & password harus diisi.")
                elif nama in db["karyawan"]:
                    st.error("Nama sudah ada.")
                else:
                    db["karyawan"][nama] = {"password": pw, "posisi": posisi, "absen": {}}
                    save_db(db)
                    st.success("Karyawan tersimpan.")

    # ----------------- Lihat Database -----------------
    elif action == "Lihat Database":
        st.subheader("📋 Lihat Database Karyawan")
        rows = []
        for name, info in db["karyawan"].items():
            rows.append({"Nama": name.title(), "Posisi": info.get("posisi",""), "Gaji (est.)": calc_month_salary(name, date.today().strftime("%Y-%m"))[0]})
        df = pd.DataFrame(rows)
        if df.empty:
            st.info("Database kosong.")
        else:
            df["Gaji (est.)"] = df["Gaji (est.)"].map(lambda x: f"{int(x):,}")
            st.dataframe(df, use_container_width=True)

    # ----------------- Edit Karyawan -----------------
    elif action == "Edit Karyawan":
        st.subheader("✏️ Edit Karyawan")
        names = [""] + [n.title() for n in db["karyawan"].keys()]
        sel = st.selectbox("Pilih karyawan", names)
        if sel:
            key = sel.lower()
            info = db["karyawan"][key]
            st.write("Posisi saat ini:", info["posisi"])
            with st.form("edit_karyawan"):
                nama_baru = st.text_input("Nama baru (kosong = tidak ubah)", value=sel).strip().lower()
                posisi_baru = st.selectbox("Posisi baru", ["intern","staff","spv","manager"], index=["intern","staff","spv","manager"].index(info["posisi"]))
                submitted = st.form_submit_button("Simpan Perubahan")
                if submitted:
                    final_name = nama_baru if nama_baru else key
                    if final_name != key:
                        db["karyawan"][final_name] = db["karyawan"].pop(key)
                    db["karyawan"][final_name]["posisi"] = posisi_baru
                    save_db(db)
                    st.success("Data diperbarui.")

    # ----------------- Hapus Karyawan -----------------
    elif action == "Hapus Karyawan":
        st.subheader("🗑 Hapus Karyawan")
        names = [""] + [n.title() for n in db["karyawan"].keys()]
        sel = st.selectbox("Pilih karyawan", names)
        if sel:
            key = sel.lower()
            if st.button("Hapus Permanen"):
                del db["karyawan"][key]
                save_db(db)
                st.success("Dihapus.")

    # ----------------- Input Pemasukan Bulanan -----------------
    elif action == "Input Pemasukan Bulanan":
        st.subheader("Input Pemasukan Bulanan")
        dt = st.date_input("Pilih bulan (pilih tanggal dalam bulan)", value=date.today())
        ym = dt.strftime("%Y-%m")
        val = st.number_input("Jumlah pemasukan (Rp)", min_value=0, value=int(db.get("pemasukan",{}).get(ym,0)))
        if st.button("Simpan Pemasukan"):
            if "pemasukan" not in db:
                db["pemasukan"] = {}
            db["pemasukan"][ym] = int(val)
            save_db(db)
            st.success("Pemasukan tersimpan.")

    # ----------------- Edit Tarif Gaji -----------------
    elif action == "Edit Tarif Gaji per Posisi":
        st.subheader("Edit Tarif Gaji (per jam)")
        st.write("Tarif saat ini (normal / overtime)")
        rates = db.get("rates", {})
        normal = rates.get("normal", {})
        overtime = rates.get("overtime", {})
        cols = st.columns(4)
        pos_list = ["intern","staff","spv","manager"]
        new_normal = {}
        new_ot = {}
        for i,p in enumerate(pos_list):
            with cols[i%4]:
                nval = st.number_input(f"{p} normal", min_value=0, value=int(normal.get(p,0)), key=f"norm_{p}")
                otval = st.number_input(f"{p} overtime", min_value=0, value=int(overtime.get(p,0)), key=f"ot_{p}")
                new_normal[p] = int(nval)
                new_ot[p] = int(otval)
        if st.button("Simpan Tarif"):
            db["rates"]["normal"] = new_normal
            db["rates"]["overtime"] = new_ot
            save_db(db)
            st.success("Tarif diperbarui.")

    elif action == "Logout Bendahara":
        st.session_state["bendahara"] = False
        st.success("Logout berhasil.")
        st.experimental_rerun()

# ---------------------
# KARYAWAN Menu
# ---------------------
elif menu == "Karyawan":
    st.header("👤 Karyawan")
    sub = st.selectbox("Aksi Karyawan", ["Login","Daftar","Absen Harian","Cek Gaji","Riwayat Kehadiran","Logout"])
    # Register / Login visible
    if sub == "Daftar":
        karyawan_register()
    elif sub == "Login":
        karyawan_login()
    else:
        # require login for certain actions
        if "karyawan" not in st.session_state or not st.session_state["karyawan"]:
            st.info("Silakan login atau daftar terlebih dahulu.")
            karyawan_login()
            st.stop()
        key = st.session_state["karyawan"]
        if sub == "Absen Harian":
            st.subheader("🗓 Absen Harian (pilih tanggal)")
            # date input (single date)
            d = st.date_input("Pilih tanggal:", value=date.today(), key="absen_date")
            dstr = d.strftime("%Y-%m-%d")
            st.write("Tanggal:", dstr)
            # status
            status = st.selectbox("Status", ["hadir","hadir+lembur","izin (sakit/cuti)"])
            overtime = 0
            if status == "hadir+lembur":
                overtime = st.number_input("Jam lembur (jam)", min_value=1, max_value=24, value=1)
            if st.button("Simpan Absen"):
                # save into db
                if "absen" not in db["karyawan"][key]:
                    db["karyawan"][key]["absen"] = {}
                db["karyawan"][key]["absen"][dstr] = {"status": status if status != "izin (sakit/cuti)" else "izin","overtime": int(overtime)}
                save_db(db)
                st.success("Absensi tersimpan.")
        elif sub == "Cek Gaji":
            st.subheader("Cek Gaji Bulanan")
            m = st.date_input("Pilih bulan (pilih tanggal di bulan yang ingin dicek)", value=date.today())
            ym = m.strftime("%Y-%m")
            total, details = calc_month_salary(key, ym)
            st.write("Nama:", key.title())
            st.write("Posisi:", db["karyawan"][key]["posisi"])
            st.write("Periode:", ym)
            st.write("Total gaji:", rp(total))
            if details:
                df = pd.DataFrame(details)
                df["amount"] = df["amount"].map(lambda x: f"{int(x):,}")
                st.table(df)
        elif sub == "Riwayat Kehadiran":
            st.subheader("Riwayat Kehadiran")
            ab = db["karyawan"][key].get("absen",{})
            if not ab:
                st.info("Belum ada riwayat absen.")
            else:
                rows = []
                for d,v in sorted(ab.items(), reverse=True):
                    rows.append({"Tanggal": d, "Status": v.get("status"), "Lembur": v.get("overtime",0)})
                st.dataframe(pd.DataFrame(rows), use_container_width=True)
        elif sub == "Logout":
            st.session_state["karyawan"] = ""
            st.success("Logout berhasil.")
            st.experimental_rerun()

# ---------------------
# Keluar
# ---------------------
elif menu == "Keluar":
    st.write("Terima kasih — tutup tab browser untuk keluar.")
