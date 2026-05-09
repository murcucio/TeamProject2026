"""Search Agent that accepts a topic and runs the paper search flow."""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.search_service import run_search


class SearchAgent:
    name = "search"

    def build_keyword(self, topic: str) -> str:
        """Normalize the user topic into a search keyword string."""
        return topic.strip()

    def run(self) -> str:
        topic = input("검색 주제를 입력하세요: ").strip()
        keyword = self.build_keyword(topic)

        print(f"입력 주제: {topic}")
        print(f"검색 키워드: {keyword}")
        print("검색 키워드로 컴퓨터 분야 논문 검색을 시작합니다.")

        run_search(keyword)
        return keyword


def main() -> None:
    agent = SearchAgent()
    agent.run()


if __name__ == "__main__":
    main()
