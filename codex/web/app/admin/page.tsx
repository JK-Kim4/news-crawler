import { AdminConsole } from "@/components/admin-console";
import { AdminOverviewPanel } from "@/components/admin-overview";
import { SectionShell } from "@/components/section-shell";
import { getAdminOverview } from "@/lib/api";

export default async function AdminPage() {
  const overview = await getAdminOverview();

  return (
    <SectionShell
      eyebrow="Ops"
      title="Crawler control room"
      description="상태 요약, 활성 소스 수, 최근 크롤링 결과를 보고 수동 트리거까지 연결할 수 있는 관리자 페이지입니다."
    >
      <div className="space-y-6">
        <AdminOverviewPanel overview={overview} />
        <AdminConsole />
      </div>
    </SectionShell>
  );
}

