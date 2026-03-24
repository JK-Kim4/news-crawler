import { ContentItem } from "@/lib/types";

type ContentDetailProps = {
  item: ContentItem;
};

export function ContentDetail({ item }: ContentDetailProps) {
  return (
    <div className="grid gap-8 lg:grid-cols-[1.5fr_0.8fr]">
      <article className="rounded-[2rem] bg-white p-8 shadow-panel">
        <div className="flex flex-wrap items-center gap-3 text-xs uppercase tracking-[0.25em] text-ink/45">
          <span>{item.source_name}</span>
          <span>{item.source_type}</span>
          <span>{item.language}</span>
        </div>
        <h1 className="mt-4 font-display text-4xl leading-tight text-ink">{item.title}</h1>
        <p className="mt-6 text-lg leading-8 text-ink/80">{item.summary}</p>
        <div className="mt-8 rounded-[1.5rem] border border-ink/10 bg-sand/60 p-6 text-sm leading-7 text-ink/75">
          {item.raw_content ?? "원문 추출 내용이 아직 없습니다."}
        </div>
      </article>
      <aside className="space-y-6">
        <div className="rounded-[2rem] bg-ink p-6 text-sand shadow-panel">
          <p className="text-xs uppercase tracking-[0.3em] text-sand/70">Tags</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {item.tags.map((tag) => (
              <span key={tag} className="rounded-full bg-white/10 px-3 py-1 text-xs uppercase tracking-[0.2em]">
                {tag}
              </span>
            ))}
          </div>
        </div>
        <div className="rounded-[2rem] bg-white p-6 shadow-panel">
          <p className="text-xs uppercase tracking-[0.3em] text-ink/40">Comments</p>
          <div className="mt-4 space-y-4">
            {(item.comments ?? []).map((comment) => (
              <div key={comment.id} className="rounded-[1rem] border border-ink/10 p-4">
                <p className="text-sm font-semibold text-ink">{comment.username}</p>
                <p className="mt-2 text-sm leading-6 text-ink/70">{comment.content}</p>
              </div>
            ))}
          </div>
        </div>
      </aside>
    </div>
  );
}

