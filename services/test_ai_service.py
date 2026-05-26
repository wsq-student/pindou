from pathlib import Path

from services.ai_service import AIService, AIServiceError


def main() -> None:
    image_path = Path(__file__).resolve().parent / "test.png"
    ai = AIService()

    print(f"使用图片: {image_path}")
    print(f"base_url: {ai.base_url}")
    print(f"model: {ai.model}")

    try:
        result = ai.analyze(image_path)
        print(f"识别成功: {len(result.beads)} 个编码")
        for item in result.beads:
            print(item)
    except AIServiceError as e:
        print(f"AIServiceError: {e}")
    except Exception as e:
        print(f"未知错误: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
