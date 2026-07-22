import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MakanReel · AI 短视频生成",
  description: "30 秒生成符合 Instagram Reels / TikTok 标准的爆款短视频",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  themeColor: "#f97316",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen font-sans text-gray-900 antialiased">
        {children}
      </body>
    </html>
  );
}
