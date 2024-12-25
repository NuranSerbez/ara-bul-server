import MainNav from "./main-nav";
import { MobileNav } from "./mobile-nav";

export default function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/10 bg-background/10 backdrop-blur supports-[backdrop-filter]:bg-background/0">
      <div className="container flex h-14 max-w-screen-2xl items-center">
        <MainNav></MainNav>
        <MobileNav></MobileNav>
      </div>
    </header>
  );
}
