import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import socket
import google.generativeai as genai

# Cấu hình API key trực tiếp từ Google AI Studio
genai.configure(api_key="AIzaSyAWXS7wjLXSUQVWa8e9k2MD1hjrL6rEkYU")

# Xác định người dùng có phải là chủ sở hữu không
is_owner = socket.gethostname() == "LAPTOP-3J8KA3L9"  # 👈 Đổi thành tên máy của bạn

def generate_analysis(prompt_text):
    try:
        with st.spinner("🔍 Đang phân tích và đánh giá"):
            model = genai.GenerativeModel("gemini-1.5-flash")
            default_instruction = (
                "Hãy phân tích dữ liệu dưới đây theo cấu trúc:\n"
                "- Đơn vị nào có kết quả tốt, đơn vị nào có kết quả yếu kém?\n"
                "- nguyên nhân của chất lượng yếu kém là gì?\n"
                "- Đề xuất hướng khắc phục cho các yếu kém đó.\n\n"
            )
            full_prompt = default_instruction + str(prompt_text)
            response = model.generate_content(full_prompt)
            return response.text
    except Exception as e:
        return f"❌ Lỗi khi gọi Google AI: {e}"

st.set_page_config(page_title="Phân tích điểm theo Trường", layout="wide")
col1, col2 = st.columns([1, 15])
with col1:
    st.image("logo.png", width=80)
with col2:
    st.markdown("## SỞ GIÁO DỤC VÀ ĐÀO TẠO TUYÊN QUANG")
st.title("📘 Phân tích điểm thi")

# Upload file chỉ cho máy chủ
import socket
is_owner = socket.gethostname() == "TEN_MAY_CUA_BAN"  # ⚠️ thay bằng tên máy của bạn

# Nếu là chủ, mới hiển thị chức năng tải dữ liệu
if is_owner:
    uploaded_file = st.file_uploader("📤 Tải file Excel", type=["xlsx", "xls"])
    if uploaded_file:
        with open("du_lieu_mau.xlsx", "wb") as f:
            f.write(uploaded_file.read())
        st.success("✅ Đã cập nhật dữ liệu thành công!")

# Load dữ liệu mẫu cho tất cả mọi người
try:
    df = pd.read_excel("du_lieu_mau.xlsx")
except:
    st.error("❌ Không tìm thấy file dữ liệu. Vui lòng upload trên máy chủ.")
    st.stop()

# Dữ liệu từ file chung
try:
    df = pd.read_excel("du_lieu_mau.xlsx")
except:
    st.error("❌ Không tìm thấy file du_lieu_mau.xlsx. Vui lòng upload trước (trên máy chủ).")
    st.stop()

# Tiền xử lý
df.columns = df.columns.str.strip()
score_columns = ['Toán', 'Văn', 'Anh', 'Lý', 'Hóa', 'Sinh', 'Sử', 'Địa', 'KTPL', 'Tin', 'CN (NN)']
for col in score_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
df['Điểm TB'] = df[score_columns].mean(axis=1, skipna=True)

# Sidebar lọc
st.sidebar.header("🔎 Bộ lọc dữ liệu")
school_options = ["Toàn tỉnh"] + sorted(df['Trường'].dropna().unique().tolist())
selected_school = st.sidebar.selectbox("Chọn phạm vi phân tích:", school_options)
df_filtered = df if selected_school == "Toàn tỉnh" else df[df['Trường'] == selected_school]

# Biểu đồ phần 1 – Trung bình theo trường
st.subheader("🏫 Biểu đồ điểm trung bình theo Trường")

avg_by_school = df_filtered.groupby("Trường")['Điểm TB'].mean()
avg_all = df_filtered['Điểm TB'].mean()
avg_by_school["Điểm TB toàn bộ"] = avg_all
avg_by_school = avg_by_school.sort_values(ascending=False)

# Đánh số thứ tự, bỏ qua dòng "Điểm TB toàn bộ"
ranked_labels = []
rank = 1
for name in avg_by_school.index:
    if name == "Điểm TB toàn bộ":
        ranked_labels.append("Trung bình")
    else:
        ranked_labels.append(f"{rank}. {name}")
        rank += 1

colors = ['orange' if name == "Điểm TB toàn bộ" else 'skyblue' for name in avg_by_school.index]

fig1, ax1 = plt.subplots(figsize=(12, 6))
bars = ax1.bar(ranked_labels, avg_by_school.values, color=colors)

for bar in bars:
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2, height + 0.2, f"{height:.2f}", ha='center', va='bottom', fontsize=9, rotation=90)

ax1.set_ylabel("Điểm trung bình")
ax1.set_title("Biểu đồ điểm trung bình theo Trường")
ax1.set_ylim(0, 10)
plt.xticks(rotation=45, ha='right')

# 👉 Tô màu chữ "Trung bình" thành cam
xtick_labels = ax1.get_xticklabels()
for label in xtick_labels:
    if label.get_text() == "Trung bình":
        label.set_color("orange")

plt.tight_layout()
st.pyplot(fig1)

# ✅ MỤC ĐÁNH GIÁ BẰNG AI
if st.checkbox("📌 Đánh giá bằng AI", key="ai1"):
    st.markdown("### 🧠 Nhận định & đề xuất từ AI:")
    st.markdown(generate_analysis(f"Dữ liệu điểm trung bình các trường: {avg_by_school.to_dict()}"))



# ======= PHẦN 2: Biểu đồ điểm trung bình theo Môn =======
st.subheader("📊 Biểu đồ điểm trung bình theo Môn")
available_subjects = [col for col in score_columns if col in df.columns]
selected_subject = st.selectbox("🎯 Chọn môn:", options=available_subjects)

if selected_subject:
    subject_avg_by_school = df_filtered.groupby("Trường")[selected_subject].mean()
    overall_subject_avg = df_filtered[selected_subject].mean()

    subject_avg_by_school["TB toàn bộ"] = overall_subject_avg
    subject_avg_by_school = subject_avg_by_school.sort_values(ascending=False)

    # Đánh số thứ tự, bỏ qua dòng "TB toàn bộ"
    ranked_labels_sub = []
    rank_sub = 1
    for name in subject_avg_by_school.index:
        if name == "TB toàn bộ":
            ranked_labels_sub.append("Trung bình")
        else:
            ranked_labels_sub.append(f"{rank_sub}. {name}")
            rank_sub += 1

    colors = ['orange' if idx == "TB toàn bộ" else 'lightgreen' for idx in subject_avg_by_school.index]

    fig2, ax2 = plt.subplots(figsize=(12, 6))
    bars2 = ax2.bar(ranked_labels_sub, subject_avg_by_school.values, color=colors)
    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2, height + 0.2, f"{height:.2f}", ha='center', va='bottom', fontsize=9, rotation=90)

    ax2.set_ylabel(f"Điểm TB môn {selected_subject}")
    ax2.set_title(f"Biểu đồ điểm trung bình môn {selected_subject} theo Trường")
    ax2.set_ylim(0, 10)
    plt.xticks(rotation=45, ha='right')

    # 👉 Tô màu chữ "Trung bình" trên trục X thành cam
    xtick_labels_sub = ax2.get_xticklabels()
    for label in xtick_labels_sub:
        if label.get_text() == "Trung bình":
            label.set_color("orange")

    plt.tight_layout()
    st.pyplot(fig2)

    if st.checkbox("📌 Đánh giá bằng AI", key="ai2"):
        st.markdown("### 🧠 Nhận định & đề xuất từ AI:")
        st.markdown(generate_analysis(f"Dữ liệu điểm trung bình môn {selected_subject} theo từng trường: {subject_avg_by_school.to_dict()}"))



# ======= PHẦN 3: Phổ điểm môn =======
st.subheader("📉 Phổ điểm từng môn")
selected_subject_hist = st.selectbox("🧪 Chọn môn để xem phổ điểm:", options=available_subjects, key="hist")
bins = st.slider("🎯 Số cột trong phổ điểm (bins):", min_value=5, max_value=30, value=30)

if selected_subject_hist:
    data = df_filtered[selected_subject_hist].dropna()
    fig_hist, ax_hist = plt.subplots(figsize=(10, 5))
    counts, bin_edges, patches = ax_hist.hist(data, bins=bins, color='steelblue', edgecolor='black')

    for count, patch in zip(counts, patches):
        bar_x = patch.get_x() + patch.get_width() / 2
        bar_height = patch.get_height()
        ax_hist.text(bar_x, bar_height + 0.5, f"{int(count)}", ha='center', va='bottom', fontsize=9)

    bin_centers = 0.5 * (bin_edges[1:] + bin_edges[:-1])
    for center in bin_centers:
        ax_hist.text(center, -0.5, f"{center:.1f}", ha='center', va='top', fontsize=9)

    ax_hist.set_title(f"Phổ điểm môn {selected_subject_hist}")
    ax_hist.set_xlabel("Điểm số")
    ax_hist.set_ylabel("Số học sinh")
    ax_hist.set_xlim(0, 10)
    ax_hist.set_ylim(bottom=0)
    plt.tight_layout()
    st.pyplot(fig_hist)
    st.info(f"🔍 Có {len(data)} học sinh có điểm môn {selected_subject_hist}")

    if st.checkbox("📌 Đánh giá bằng AI", key="ai3"):
        st.markdown("### 🧠 Nhận định & đề xuất từ AI:")
        st.markdown(generate_analysis(f"Phổ điểm môn {selected_subject_hist}: {counts.tolist()}"))

# ======= PHẦN 4: Điểm trung bình từng môn =======
st.subheader("📚 Điểm trung bình các môn thi")
subject_means_filtered = df_filtered[score_columns].mean()
subject_means_all = df[score_columns].mean()

fig4, ax4 = plt.subplots(figsize=(10, 5))
x = range(len(score_columns))
bar_width = 0.35

bars_filtered = ax4.bar([i - bar_width/2 for i in x], subject_means_filtered.values, width=bar_width, label="Trường đã chọn", color='mediumseagreen')
bars_all = ax4.bar([i + bar_width/2 for i in x], subject_means_all.values, width=bar_width, label="Toàn tỉnh", color='orange')

for i, (bar1, bar2) in enumerate(zip(bars_filtered, bars_all)):
    ax4.text(bar1.get_x() + bar1.get_width()/2, bar1.get_height() + 0.2, f"{bar1.get_height():.2f}", ha='center', va='bottom', fontsize=9, rotation=90)
    ax4.text(bar2.get_x() + bar2.get_width()/2, bar2.get_height() + 0.2, f"{bar2.get_height():.2f}", ha='center', va='bottom', fontsize=9, rotation=90)

ax4.set_xticks(list(x))
ax4.set_xticklabels(score_columns, rotation=0)
ax4.set_title("Biểu đồ điểm trung bình các môn học")
ax4.set_ylabel("Điểm trung bình")
ax4.set_ylim(0, 10)
ax4.legend()
plt.tight_layout()
st.pyplot(fig4)

if st.checkbox("📌 Đánh giá bằng AI", key="ai4"):
    st.markdown("### 🧠 Nhận định & đề xuất từ AI:")
    st.markdown(generate_analysis(f"So sánh điểm trung bình các môn thi giữa trường '{selected_school}' và toàn tỉnh.\nTrường: {subject_means_filtered.to_dict()}\nToàn tỉnh: {subject_means_all.to_dict()}"))

# ====== CHÂN TRANG ======
st.markdown("---")
st.markdown("©️ **Bản quyền thuộc về iTeX-Teams**", unsafe_allow_html=True)