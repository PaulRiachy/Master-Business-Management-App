import "./globals.css";
import { AppShell } from "@/components/app-shell";
export const metadata = { title: "Master Business Management", description: "Internal project lifecycle management MVP" };
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body><AppShell>{children}</AppShell></body></html>}
