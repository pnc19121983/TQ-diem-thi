import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import socket
import google.generativeai as genai
import os
import plotly.graph_objects as go

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
                "- Căn cứ vào điểm trung bình, phương sai, độ lệch chuẩn, số trung vị, mốt, khoảng biến thiên, khoản tứ phân vị đưa ra nhận xét đánh giá\n"
                "- Nguyên nhân của Chưa đạt là gì?\n"
                "- Đề xuất hướng khắc phục cho các đối tượng Chưa đạt đó.\n\n"
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

# ======= PHẦN 7: Thống kê số lượng thí sinh chọn môn tổ hợp (trừ Toán, Văn) =======
st.subheader("📈 Thống kê số lượng thí sinh lựa chọn các môn tổ hợp")

# Loại bỏ các môn bắt buộc
excluded_subjects = ["Toán", "Văn"]
optional_subjects = [col for col in score_columns if col not in excluded_subjects and col in df.columns]

# Đếm số thí sinh có điểm, chỉ giữ môn có ít nhất 1 thí sinh chọn
subject_counts = {
    subject: df_filtered[subject].notna().sum()
    for subject in optional_subjects
    if df_filtered[subject].notna().sum() > 0
}

if not subject_counts:
    st.warning("❗ Không có dữ liệu môn tự chọn nào để thống kê.")
else:
    # Dữ liệu cho biểu đồ
    labels = list(subject_counts.keys())
    sizes = list(subject_counts.values())
    colors = plt.get_cmap("tab20")(range(len(labels)))

    # Tạo biểu đồ tròn rõ nét
    fig7, ax7 = plt.subplots(figsize=(6, 3), dpi=200)
    wedges, texts, autotexts = ax7.pie(
        sizes,
        labels=labels,
        autopct='%1.1f%%',
        startangle=140,
        colors=colors,
        textprops=dict(color="black", fontsize=6)
    )

    ax7.axis('equal')
    ax7.set_title("Tỷ lệ lựa chọn các môn tổ hợp", fontsize=8)

    # Canh lề đẹp
    plt.tight_layout()
    st.pyplot(fig7)

    # Đánh giá AI
    if st.checkbox("📌 Đánh giá bằng AI", key="ai7"):
        st.markdown("### 🧠 Nhận định & đề xuất từ AI:")
        st.markdown(generate_analysis(
            f"Số lượng thí sinh chọn thi từng môn tổ hợp (trừ Toán, Văn): {subject_counts}"
        ))





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
bins = st.slider("🎯 Số cột trong phổ điểm:", min_value=5, max_value=30, value=30)

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


# ======= PHẦN 5: Điểm trung bình của từng lớp trong một trường =======
if selected_school != "Toàn tỉnh":
    st.subheader("🏫 Điểm trung bình của từng lớp trong trường")

    if 'Lớp' not in df_filtered.columns:
        st.warning("❗ Dữ liệu chưa có cột 'Lớp'. Vui lòng kiểm tra lại file.")
    else:
        class_avg = df_filtered.groupby("Lớp")['Điểm TB'].mean().sort_values(ascending=False)
        overall_avg = df['Điểm TB'].mean()

        fig5, ax5 = plt.subplots(figsize=(12, 6))
        bars_class = ax5.bar(class_avg.index, class_avg.values, color='lightcoral')

        ax5.axhline(overall_avg, color='orange', linestyle='--', label=f"Trung bình toàn tỉnh: {overall_avg:.2f}")

        for bar in bars_class:
            height = bar.get_height()
            ax5.text(bar.get_x() + bar.get_width()/2, height + 0.2, f"{height:.2f}", ha='center', va='bottom', fontsize=9, rotation=90)

        ax5.set_title(f"Biểu đồ điểm trung bình các lớp trong trường {selected_school}")
        ax5.set_ylabel("Điểm trung bình")
        ax5.set_ylim(0, 10)
        ax5.legend()
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        st.pyplot(fig5)

        if st.checkbox("📌 Đánh giá bằng AI", key="ai5"):
            st.markdown("### 🧠 Nhận định & đề xuất từ AI:")
            st.markdown(generate_analysis(
                f"Điểm trung bình các lớp trong trường {selected_school}: {class_avg.to_dict()}\n"
                f"Trung bình toàn tỉnh: {overall_avg}"
            ))
else:
    st.info("📌 Vui lòng chọn một trường cụ thể để xem thống kê theo lớp.")


# ======= PHẦN 6: So sánh điểm trung bình từng môn học giữa các lớp =======
if selected_school != "Toàn tỉnh":
    st.subheader("🏫 So sánh điểm trung bình từng môn học giữa các lớp trong trường")

    if 'Lớp' not in df_filtered.columns:
        st.warning("❗ Dữ liệu chưa có cột 'Lớp'. Vui lòng kiểm tra lại file.")
    else:
        class_subject_means = df_filtered.groupby("Lớp")[score_columns].mean()
        selected_sub6 = st.selectbox("🧪 Chọn môn học:", options=score_columns, key="sub6")
        data_sub = class_subject_means[selected_sub6]
        avg_all_sub = subject_means_all[selected_sub6]

        fig6_sub, ax6_sub = plt.subplots(figsize=(12, 6))
        bars_sub = ax6_sub.bar(data_sub.index, data_sub.values, color='skyblue')
        ax6_sub.axhline(avg_all_sub, color='orange', linestyle='--', label=f"Trung bình toàn tỉnh: {avg_all_sub:.2f}")

        for bar in bars_sub:
            height = bar.get_height()
            ax6_sub.text(bar.get_x() + bar.get_width()/2, height + 0.2, f"{height:.2f}", ha='center', va='bottom', fontsize=9, rotation=90)

        ax6_sub.set_title(f"Điểm trung bình môn {selected_sub6} theo lớp - Trường {selected_school}")
        ax6_sub.set_ylabel("Điểm trung bình")
        ax6_sub.set_ylim(0, 10)
        ax6_sub.legend()
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        st.pyplot(fig6_sub)

        if st.checkbox("📌 Đánh giá bằng AI", key="ai6_sub"):
            st.markdown("### 🧠 Nhận định & đề xuất từ AI:")
            st.markdown(generate_analysis(
                f"Điểm trung bình môn {selected_sub6} theo lớp trong trường {selected_school}: {data_sub.to_dict()}\n"
                f"Trung bình toàn tỉnh môn {selected_sub6}: {avg_all_sub}"
            ))
else:
    st.info("📌 Vui lòng chọn một trường cụ thể để xem thống kê theo lớp.")

# ======= PHẦN 8: So sánh điểm trung bình giữa các Trường qua các lần thi =======
st.subheader("📊 So sánh điểm trung bình giữa các Trường qua các Lần thi")

# Danh sách các file và nhãn tương ứng
labels = ["Lần 1", "Lần 2", "Lần 3"]
file_names = ["du_lieu_mau.xlsx", "du_lieu_mau_1.xlsx", "du_lieu_mau_2.xlsx"]
data_versions = []

# Đọc từng file nếu tồn tại
for file, label in zip(file_names, labels):
    if not os.path.exists(file):
        st.warning(f"⚠️ Không tìm thấy file: `{file}`")
        continue

    try:
        df_temp = pd.read_excel(file)
        df_temp.columns = df_temp.columns.str.strip()

        if "Trường" not in df_temp.columns:
            st.error(f"❌ File `{file}` thiếu cột 'Trường'")
            continue

        for col in score_columns:
            if col in df_temp.columns:
                df_temp[col] = pd.to_numeric(df_temp[col], errors='coerce')

        df_temp['Điểm TB'] = df_temp[score_columns].mean(axis=1, skipna=True)
        df_temp["Lần thi"] = label
        data_versions.append(df_temp)

    except Exception as e:
        st.error(f"❌ Lỗi khi đọc file `{file}`: {e}")

if len(data_versions) < 2:
    st.info("📌 Cần ít nhất 2 file dữ liệu hợp lệ để so sánh.")
    st.stop()

# Gộp dữ liệu
df_all_cmp = pd.concat(data_versions, ignore_index=True)

# Trung bình theo Trường và Lần thi
avg_by_school_exam = df_all_cmp.groupby(["Trường", "Lần thi"])["Điểm TB"].mean().unstack()

# Biểu đồ Plotly – Tổng hợp điểm TB theo Trường và Lần thi
fig_cmp_grouped = go.Figure()
x_labels = avg_by_school_exam.index.tolist()

for i, exam_label in enumerate(avg_by_school_exam.columns):
    fig_cmp_grouped.add_trace(go.Bar(
        name=exam_label,
        x=x_labels,
        y=avg_by_school_exam[exam_label],
        hovertemplate="Trường: %{x}<br>Lần thi: " + exam_label + "<br>Điểm TB: %{y:.2f}<extra></extra>"
    ))

fig_cmp_grouped.update_layout(
    barmode='group',
    title="So sánh điểm trung bình giữa các Trường qua các Lần thi",
    xaxis_title="Trường",
    yaxis_title="Điểm trung bình",
    yaxis=dict(range=[0, 10]),
    xaxis_tickangle=45,
    hovermode="x unified"
)
st.plotly_chart(fig_cmp_grouped, use_container_width=True)

# Đánh giá bằng AI
if st.checkbox("📌 Đánh giá bằng AI", key="ai_cmp_all_schools"):
    st.markdown("### 🧠 Nhận định & đề xuất từ AI:")
    st.markdown(generate_analysis(
        f"Điểm trung bình các Trường qua các Lần thi:\n{avg_by_school_exam.to_dict(orient='index')}"
    ))

# ======= MỞ RỘNG: So sánh môn học giữa các Trường qua các Lần thi =======
st.markdown("### 📘 So sánh điểm trung bình từng môn giữa các Trường qua các Lần thi")

selected_subject_across = st.selectbox(
    "🎯 Chọn môn học để so sánh:",
    options=[col for col in score_columns if col in df_all_cmp.columns],
    key="cmp_subject_across"
)

# Trung bình theo Trường, Lần thi cho môn chọn
subject_avg_across = df_all_cmp.groupby(["Trường", "Lần thi"])[selected_subject_across].mean().unstack()

# Biểu đồ Plotly – môn học cụ thể
fig_sub_cmp = go.Figure()
x_labels = subject_avg_across.index.tolist()

for i, exam_label in enumerate(subject_avg_across.columns):
    fig_sub_cmp.add_trace(go.Bar(
        name=exam_label,
        x=x_labels,
        y=subject_avg_across[exam_label],
        hovertemplate=f"Trường: %{{x}}<br>Lần thi: {exam_label}<br>Điểm TB {selected_subject_across}: %{{y:.2f}}<extra></extra>"
    ))

fig_sub_cmp.update_layout(
    barmode='group',
    title=f"So sánh điểm trung bình môn {selected_subject_across} giữa các Trường qua các Lần thi",
    xaxis_title="Trường",
    yaxis_title=f"Điểm TB môn {selected_subject_across}",
    yaxis=dict(range=[0, 10]),
    xaxis_tickangle=45,
    hovermode="x unified"
)
st.plotly_chart(fig_sub_cmp, use_container_width=True)

# Đánh giá bằng AI
if st.checkbox("📌 Đánh giá bằng AI", key="ai_cmp_subject_across"):
    st.markdown("### 🧠 Nhận định & đề xuất từ AI:")
    st.markdown(generate_analysis(
        f"Điểm trung bình môn {selected_subject_across} của các Trường qua các Lần thi:\n{subject_avg_across.to_dict(orient='index')}"
    ))



# ====== CHÂN TRANG ======
st.markdown("---")
st.markdown("©️ **Bản quyền thuộc về iTeX-Teams**", unsafe_allow_html=True)