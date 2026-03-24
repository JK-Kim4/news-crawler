import { AuthPanel } from "@/components/auth-panel";
import { SectionShell } from "@/components/section-shell";

export default function LoginPage() {
  return (
    <SectionShell
      eyebrow="Access"
      title="Sign in"
      description="JWT 토큰을 발급받아 북마크, 알림 설정, 관리자 트리거를 사용할 수 있습니다."
    >
      <AuthPanel mode="login" />
    </SectionShell>
  );
}

