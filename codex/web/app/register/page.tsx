import { AuthPanel } from "@/components/auth-panel";
import { SectionShell } from "@/components/section-shell";

export default function RegisterPage() {
  return (
    <SectionShell
      eyebrow="Access"
      title="Create account"
      description="기본 가입은 일반 사용자 역할로 생성되며, 관리자 권한은 백엔드에서 별도로 관리합니다."
    >
      <AuthPanel mode="register" />
    </SectionShell>
  );
}

