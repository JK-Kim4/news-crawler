import { ContentItem } from "@/lib/types";

type ArticleCardProps = {
  item: ContentItem;
};

export function ArticleCard({ item }: ArticleCardProps) {
  return (
    <article className="flex h-full flex-col justify-between rounded-[1.5rem] border border-ink/10 bg-white p-6 shadow-panel">
      <div className="space-y-4">
        <div className="flex items-center justify-between text-xs uppercase tracking-[0.25em] text-ink/45">
          <span>{item.source_name}</span>
          <span>{item.language}</span>
        </div>
        <div className="space-y-3">
          <h3 className="font-display text-2xl leading-tight text-ink">
            <a href={`/content/${item.id}`}>{item.title}</a>
          </h3>
          <p className="text-sm leading-7 text-ink/75">{item.summary}</p>
        </div>
      </div>
      <div className="mt-6 flex flex-wrap gap-2">
        {item.tags.map((tag) => (
          <span key={tag} className="rounded-full bg-mist px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-moss">
            {tag}
          </span>
        ))}
      </div>
    </article>
  );
}

