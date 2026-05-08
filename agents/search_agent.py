"""Search Agent that accepts a topic and calls the arXiv search service."""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.search_service import demo_arxiv_search


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
        print("검색 키워드가 API 요청에 사용될 준비가 되었습니다.")

        demo_arxiv_search(keyword)
        return keyword


def main() -> None:
    agent = SearchAgent()
    agent.run()


if __name__ == "__main__":
    main()
