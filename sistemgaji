# app.py  (paste ini ke file app.py atau sistemgaji.py)
import streamlit as st
import json
import os
import pandas as pd

# ---------------------------
# Konfigurasi file database
# ---------------------------
DATA_FILE = "databaseghe1.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ---------------------------
# Tarif gaji normal & lembur
# ---------------------------
def gaji_normal(posisi):
    p = posisi.lower()
    if p == "intern": return 35000
    if p == "staff": return 50000
    if p == "spv": return 100000
    if p == "manager": return 200000
    return 0

def gaji_lembur(posisi):
    p = posisi.lower()
    if p == "intern": return 20000
    if p == "staff": return 40000
    if p == "spv": return 55000
    if p == "manager": return 65000
    return 0

# ---------------------------
# Hitung gaji bulanan dari data 4 minggu
# weeks = list of dicts: [{"days":int,"overtime":int}, ...]
# ---------------------------
def calculate_monthly(posisi, weeks):
    total = 0
    for w in weeks:
        days = int(w.get("days", 0))
        overtime = int(w.get("overtime", 0))
        jam_normal = days * 8
        gaji_minggu = (jam_normal * gaji_normal(posisi)) + (overtime * gaji_lembur(posisi))
        total += gaji_minggu
    return total

# ---------------------------
# Utility formatting
# ---------------------------
def rp(x):
    try:
        return f"Rp {int(x):,}"
    except:
        return f"Rp {x}"

# ---------------------------
# Session state init
# ---------------------------
if "bendahara_logged" not in st.session_state:
    st.session_state.bendahara_logged = False
if "bendahara_email" not in st.session_state:
    st.session_state.bendahara_email = ""

# ---------------------------
# Layout & Sidebar
# ---------------------------
st.set_page_config(page_title="Sistem Gaji - Dashboard", layout="wide")
st.title("💼 Sistem Gaji Karyawan — Dashboard")

menu = st.sidebar.radio("Navigasi", ["Beranda", "Bendahara", "Karyawan", "Tentang"])

# Load DB
db = load_data()  # dict: {name: {"posisi":..., "gaji":..., "weeks":[...]}}

# ---------------------------
# BERANDA
# ---------------------------
if menu == "Beranda":
    st.header("Selamat datang!")
    st.write("Gunakan sidebar untuk pindah ke menu **Bendahara** (input/edit/hapus) atau **Karyawan** (cek gaji).")
    st.markdown("---")
    st.subheader("Ringkasan singkat")
    total_karyawan = len(db)
    total_payroll = sum(item.get("gaji", 0) for item in db.values())
    col1, col2 = st.columns(2)
    col1.metric("Jumlah Karyawan", total_karyawan)
    col2.metric("Total Gaji Bulanan (estimasi)", rp(total_payroll))

# ---------------------------
# BENDAHARA
# ---------------------------
elif menu == "Bendahara":
    st.header("🔐 Menu Bendahara")
    # Login sederhana
    if not st.session_state.bendahara_logged:
        st.subheader("Login Bendahara")
        with st.form("login_form"):
            email = st.text_input("Email")
            pw = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                # kredensial contoh (ubah sesuai kebutuhan)
                if email.strip().lower() == "bendahara@email.com" and pw == "12345":
                    st.session_state.bendahara_logged = True
                    st.session_state.bendahara_email = email
                    st.success("Login berhasil!")
                else:
                    st.error("Email atau password salah.")
        st.stop()

    # Setelah login
    st.info(f"Login sebagai: {st.session_state.bendahara_email}")
    action = st.selectbox("Aksi Bendahara", ["Input Data Karyawan", "Lihat Database", "Edit Data Karyawan", "Hapus Data Karyawan", "Logout"])

    # ---------- Input Data ----------
    if action == "Input Data Karyawan":
        st.subheader("➕ Input Data Karyawan (4 minggu)")
        with st.form("input_karyawan", clear_on_submit=False):
            nama = st.text_input("Nama karyawan").strip().lower()
            posisi = st.selectbox("Posisi", ["intern", "staff", "spv", "manager"])
            st.markdown("**Masukkan data per minggu (hari masuk & jam lembur)**")
            weeks = []
            cols = st.columns(4)
            for i in range(4):
                with cols[i]:
                    d = st.number_input(f"Minggu {i+1} - Hari masuk", min_value=0, max_value=7, value=5, key=f"days_{i}")
                    o = st.number_input(f"Minggu {i+1} - Jam lembur", min_value=0, max_value=100, value=0, key=f"overtime_{i}")
                weeks.append({"days": int(d), "overtime": int(o)})
            submit = st.form_submit_button("Simpan Data")
            if submit:
                if not nama:
                    st.warning("Masukkan nama karyawan.")
                else:
                    total = calculate_monthly(posisi, weeks)
                    db[nama] = {"posisi": posisi, "gaji": total, "weeks": weeks}
                    save_data(db)
                    st.success(f"Data {nama.title()} tersimpan. Total gaji bulan: {rp(total)}")

    # ---------- Lihat Database ----------
    elif action == "Lihat Database":
        st.subheader("📋 Database Karyawan")
        if not db:
            st.info("Database kosong.")
        else:
            # Show as table
            rows = []
            for name, item in db.items():
                rows.append({
                    "Nama": name.title(),
                    "Posisi": item.get("posisi", ""),
                    "Gaji (Rp)": item.get("gaji", 0)
                })
            df = pd.DataFrame(rows)
            df["Gaji (Rp)"] = df["Gaji (Rp)"].map(lambda x: f"{int(x):,}")
            st.dataframe(df, use_container_width=True)
            st.markdown("---")
            st.write("Klik salah satu nama di bawah untuk melihat detail mingguannya.")
            sel = st.selectbox("Pilih karyawan untuk detail", [""] + [n.title() for n in db.keys()])
            if sel:
                key = sel.lower()
                item = db[key]
                st.write(f"**Nama:** {sel}")
                st.write(f"**Posisi:** {item['posisi']}")
                st.write(f"**Gaji Bulanan:** {rp(item['gaji'])}")
                st.markdown("**Rincian Mingguan:**")
                week_df = pd.DataFrame(item.get("weeks", []))
                week_df.index = [f"Minggu {i+1}" for i in range(len(week_df))]
                st.table(week_df)

    # ---------- Edit Data ----------
    elif action == "Edit Data Karyawan":
        st.subheader("✏️ Edit Data Karyawan")
        if not db:
            st.info("Database kosong.")
        else:
            pilihan = st.selectbox("Pilih karyawan untuk diedit", [""] + [n.title() for n in db.keys()])
            if pilihan:
                key = pilihan.lower()
                item = db[key]
                st.write("Data saat ini:")
                st.write(f"- Nama: {pilihan}")
                st.write(f"- Posisi: {item['posisi']}")
                st.write(f"- Gaji: {rp(item['gaji'])}")
                st.markdown("**Ubah data**")
                with st.form("edit_form"):
                    nama_baru = st.text_input("Nama baru (biarkan kosong jika tidak ingin ubah)", value=pilihan).strip().lower()
                    posisi_baru = st.selectbox("Posisi baru", ["intern","staff","spv","manager"], index=["intern","staff","spv","manager"].index(item['posisi']))
                    # allow recalc weeks
                    st.write("Ubah minggu (opsional, kosongkan untuk pakai data lama)")
                    new_weeks = []
                    cols = st.columns(4)
                    existing_weeks = item.get("weeks", [{"days":0,"overtime":0}]*4)
                    for i in range(4):
                        with cols[i]:
                            d = st.number_input(f"Minggu {i+1} - Hari masuk", min_value=0, max_value=7, value=existing_weeks[i].get("days",0), key=f"edit_days_{key}_{i}")
                            o = st.number_input(f"Minggu {i+1} - Jam lembur", min_value=0, max_value=200, value=existing_weeks[i].get("overtime",0), key=f"edit_ot_{key}_{i}")
                        new_weeks.append({"days":int(d), "overtime":int(o)})
                    submit_edit = st.form_submit_button("Simpan Perubahan")
                    if submit_edit:
                        # apply changes
                        final_name = nama_baru if nama_baru else key
                        # if name changed and different key, rename entry
                        if final_name != key:
                            db[final_name] = db.pop(key)
                        db[final_name]["posisi"] = posisi_baru
                        db[final_name]["weeks"] = new_weeks
                        db[final_name]["gaji"] = calculate_monthly(posisi_baru, new_weeks)
                        save_data(db)
                        st.success("Data berhasil diperbarui.")
                        st.experimental_rerun()

    # ---------- Hapus Data ----------
    elif action == "Hapus Data Karyawan":
        st.subheader("🗑 Hapus Data Karyawan")
        if not db:
            st.info("Database kosong.")
        else:
            pilih = st.selectbox("Pilih karyawan untuk dihapus", [""] + [n.title() for n in db.keys()])
            if pilih:
                key = pilih.lower()
                if st.button("Hapus Permanen"):
                    del db[key]
                    save_data(db)
                    st.success(f"Data {pilih} telah dihapus.")
                    st.experimental_rerun()

    # ---------- Logout ----------
    elif action == "Logout":
        st.session_state.bendahara_logged = False
        st.session_state.bendahara_email = ""
        st.success("Berhasil logout.")
        st.experimental_rerun()

# ---------------------------
# KARYAWAN
# ---------------------------
elif menu == "Karyawan":
    st.header("👤 Menu Karyawan — Cek Gaji")
    nama = st.text_input("Masukkan nama (tanpa gelar):").strip().lower()
    if st.button("Cek Gaji"):
        if not nama:
            st.warning("Masukkan nama Anda.")
        elif nama in db:
            item = db[nama]
            st.success("Data ditemukan:")
            st.write("Nama :", nama.title())
            st.write("Posisi :", item["posisi"])
            st.write("Gaji Bulanan :", rp(item["gaji"]))
            st.markdown("**Rincian Mingguan**")
            week_df = pd.DataFrame(item.get("weeks", []))
            week_df.index = [f"Minggu {i+1}" for i in range(len(week_df))]
            st.table(week_df)
        else:
            st.error("Nama tidak ditemukan di database. Hubungi bendahara untuk input data.")

# ---------------------------
# TENTANG
# ---------------------------
elif menu == "Tentang":
    st.header("Tentang Aplikasi")
    st.write("""
    Aplikasi ini dibuat dengan Streamlit untuk demo Sistem Gaji sederhana.
    Fitur:
    - Bendahara: login, input data karyawan (masuk 4 minggu), lihat/edit/hapus data
    - Karyawan: cek gaji berdasarkan nama
    - Data disimpan di file JSON: databaseghe1.json
    """)
    st.write("Cara deploy: pasang file ini di repository GitHub, lalu hubungkan ke Streamlit Cloud. Pastikan file requirements.txt berisi `streamlit` dan `pandas`.")

# ---------------------------
# Akhir - simpan sebelum exit
# ---------------------------
# (simpan otomatis pada setiap perubahan sudah dilakukan di fungsi save_data)
