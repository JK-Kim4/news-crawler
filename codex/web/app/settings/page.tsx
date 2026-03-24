import { SectionShell } from "@/components/section-shell";
import { SettingsPanel } from "@/components/settings-panel";
import { getNotificationPreference } from "@/lib/api";

export default async function SettingsPage() {
  const preference = await getNotificationPreference();

  return (
    <SectionShell
      eyebrow="Alerts"
      title="Notification preferences"
      description="관심 키워드와 수신 채널을 저장해 새 요약이 들어왔을 때 바로 확인할 수 있게 준비합니다."
    >
      <SettingsPanel preference={preference} />
    </SectionShell>
  );
}

