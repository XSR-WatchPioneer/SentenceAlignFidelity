from mistralai import Mistral
from pathlib import Path
import os
import base64
from mistralai import DocumentURLChunk
from mistralai.models import OCRResponse
# pip install mistralai
from LLM_API import Mistral_OCR_API
from utils import select_pdf
def replace_images_in_markdown(markdown_str: str, images_dict: dict) -> str:
    for img_name, img_path in images_dict.items():
        markdown_str = markdown_str.replace(f"![{img_name}]({img_name})", f"![{img_name}]({img_path})")
    return markdown_str


def save_ocr_results(ocr_response: OCRResponse, pdf_path: str) -> None:
    # 获取PDF文件的目录和文件名
    pdf_file = Path(pdf_path)
    pdf_dir = pdf_file.parent
    pdf_name = pdf_file.stem

    # 创建图片目录（PDF文件名.assets）
    images_dir = pdf_dir / f"{pdf_name}.assets"
    os.makedirs(images_dir, exist_ok=True)

    all_markdowns = []
    for page in ocr_response.pages:
        # 保存图片
        page_images = {}
        for img in page.images:
            img_data = base64.b64decode(img.image_base64.split(',')[1])
            img_path = images_dir / f"{img.id}.png"
            with open(img_path, 'wb') as f:
                f.write(img_data)
            page_images[img.id] = f"{pdf_name}.assets/{img.id}.png"

        # 处理markdown内容
        page_markdown = replace_images_in_markdown(page.markdown, page_images)
        all_markdowns.append(page_markdown)

    # 保存完整markdown
    markdown_path = pdf_dir / f"{pdf_name}.md"
    with open(markdown_path, 'w', encoding='utf-8') as f:
        f.write("\n\n".join(all_markdowns))


def pdf2markdown(pdf_path: str, api_key: str) -> None:
    # 初始化客户端
    client = Mistral(api_key=api_key)

    # 确认PDF文件存在
    pdf_file = Path(pdf_path)
    if not pdf_file.is_file():
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

    # 上传并处理PDF
    uploaded_file = client.files.upload(
        file={
            "file_name": pdf_file.stem,
            "content": pdf_file.read_bytes(),
        },
        purpose="ocr",
    )

    signed_url = client.files.get_signed_url(file_id=uploaded_file.id, expiry=1)
    pdf_response = client.ocr.process(
        document=DocumentURLChunk(document_url=signed_url.url),
        model="mistral-ocr-latest",
        include_image_base64=True
    )

    # 保存结果
    save_ocr_results(pdf_response, pdf_path)
    print(f"PDF转Markdown处理完成。结果保存为: {pdf_file.parent / f'{pdf_file.stem}.md'}")


if __name__ == "__main__":
    # 使用示例
    API_KEY = Mistral_OCR_API
    PDF_PATH = select_pdf()

    pdf2markdown(PDF_PATH, API_KEY)
