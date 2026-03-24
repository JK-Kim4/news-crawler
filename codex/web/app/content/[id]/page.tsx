import { ContentDetail } from "@/components/content-detail";
import { getContent } from "@/lib/api";

export default async function ContentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const item = await getContent(id);

  return <ContentDetail item={item} />;
}

