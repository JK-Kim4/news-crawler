import { ArticleCard } from "@/components/article-card";
import { SectionShell } from "@/components/section-shell";
import { getContents } from "@/lib/api";

export default async function HomePage() {
  const contents = await getContents();

  return (
    <>
      <section className="rounded-[2.5rem] bg-ink px-8 py-12 text-sand shadow-panel">
        <p className="text-xs uppercase tracking-[0.4em] text-sand/60">Live Desk</p>
        <h1 className="mt-4 max-w-3xl font-display text-5xl leading-tight">
          국내 기술 블로그와 글로벌 AI 리서치를 한 화면에서 읽는 요약 피드.
        </h1>
        <p className="mt-6 max-w-2xl text-sm leading-8 text-sand/75">
          수집, 요약, 검색, 북마크, 관리자 수동 트리거까지 한 번에 묶은 제품형 MVP입니다.
        </p>
      </section>

      <SectionShell
        eyebrow="Today"
        title="Curated feed"
        description="활성 소스에서 수집된 콘텐츠를 요약 중심으로 배열합니다. 한국어 소스를 먼저 노출하는 구성을 기본값으로 둡니다."
      >
        <div className="grid gap-5 lg:grid-cols-2">
          {contents.map((item) => (
            <ArticleCard key={item.id} item={item} />
          ))}
        </div>
      </SectionShell>
    </>
  );
}

