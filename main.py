import openai
import yaml
import os
from dotenv import load_dotenv

load_dotenv('env.env')
OPEN_API_KEY = os.getenv("OPENAI_API_KEY")
OPEN_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME")


client = openai.OpenAI(api_key=OPEN_API_KEY)

def read_task_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def build_prompt(task_yaml):
    # Trích xuất thông tin cần thiết từ task_yaml
    task_type = task_yaml['task_description']['type']
    description = task_yaml['task_description']['description']
    input_desc = task_yaml['task_description']['input']
    output_desc = task_yaml['task_description']['output']
    visualize = task_yaml['task_description']['visualize']['description']
    features = task_yaml['task_description']['visualize']['features']
    api_url = task_yaml['model_information']['api_url']
    input_format = task_yaml['model_information']['input_format']
    output_format = task_yaml['model_information']['output_format']
    dataset_path = task_yaml['dataset_description'].get('data_path', task_yaml['dataset_description'].get('data_source'))
    # dataset_path = "./data/goemotions.csv"

    prompt = f"""
Bạn là một lập trình viên Python chuyên nghiệp. Hãy sinh code Streamlit hoàn chỉnh cho bài toán sau:

- Loại bài toán: {task_type}
- Mô tả: {description}
- Input: {input_desc}
- Output: {output_desc}
- Yêu cầu giao diện: {visualize}
- Các tính năng: {features}
- API model: {api_url}
- Định dạng input model: {input_format}
- Định dạng output model: {output_format}
- Dataset ví dụ: {dataset_path}

Yêu cầu:
- Cho payload của các post response, cần chú ý lấy đúng payload để tránh gây lỗi 422 (ví dụ: image chỉ cần payload là "data", text chỉ cần payload là "text" tương ứng)
- Gửi dữ liệu tới API model, nhận kết quả, hiển thị nhãn/kết quả/xác suất.
- Cần kiểm tra data api trả về (data thường lồng list trong list) có đúng chuẩn kì vọng (len, shape) không, nếu chưa đúng, reshape hoặc sử dụng các phương thức khác để đảm bảo input.
- Hiển thị danh sách các input và kết quả dự đoán.
- Đọc file dataset ví dụ, hiển thị một số ví dụ minh họa.
- Code phải hoàn chỉnh, có thể chạy ngay với `streamlit run`.
- Có chú thích rõ ràng.
- Với task text classification cần chú ý các tên các trường emotion.
- Chú ý đoạn code trả về không được chứa hướng dẫn, markdown và có thể chạy ngay được với streamlit run
- Tuyệt đối không sử dụng `st.cache`, thay vào đó hãy sử dụng `st.cache_data` để cache dữ liệu (ví dụ: dataframes, JSON) và `st.cache_resource` để cache các tài nguyên không thể tuần tự hóa (ví dụ: model, database connection).
- Khi hiển thị hình ảnh hoặc các đối tượng media khác, hãy sử dụng tham số `use_container_width=True` thay vì `use_column_width` đã lỗi thời để co giãn theo chiều rộng của khung chứa.
"""
    return prompt

def call_llm(prompt):
    # Gọi OpenAI API hoặc LLM khác
    response = client.chat.completions.create(
        model=OPEN_MODEL_NAME,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def main(task_yaml_path='task.yaml'):
    # This function now returns the generated code as a string
    # instead of writing it to a file.
    task_yaml = read_task_yaml(task_yaml_path)
    prompt = build_prompt(task_yaml)
    code_string = call_llm(prompt)
    
    # The cleaning logic can now operate on the string directly
    lines = code_string.splitlines(True)
    if len(lines) >= 2:
        if lines[0].strip().startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
    
    cleaned_code = "".join(lines)
    print("✅ Code generated and cleaned successfully.")
    return cleaned_code

if __name__ == "__main__":
    # For standalone testing if needed
    generated_code = main()
    with open('generated_ui_standalone.py', 'w', encoding='utf-8') as f:
        f.write(generated_code)
    print("Generated code saved to generated_ui_standalone.py for testing.")