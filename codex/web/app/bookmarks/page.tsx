import { ArticleCard } from "@/components/article-card";
import { SectionShell } from "@/components/section-shell";
import { getBookmarks } from "@/lib/api";

export default async function BookmarksPage() {
  const contents = await getBookmarks();

  return (
    <SectionShell
      eyebrow="Library"
      title="Bookmarked stories"
      description="북마크 컬렉션은 개인 큐레이션 보드처럼 동작합니다. 실제 API 연결 시 사용자 토큰 기준으로 내려옵니다."
    >
      <div className="grid gap-5 lg:grid-cols-2">
        {contents.map((item) => (
          <ArticleCard key={item.id} item={item} />
        ))}
      </div>
    </SectionShell>
  );
}

