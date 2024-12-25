import { Link, NavLink } from "@remix-run/react";

export default function MainNav() {
  return (
    <div className="mr-4 hidden md:flex">
      <Link to="/" className="mr-14 flex items-center space-x-2">
        <div className="text-black font-bold">Ara-Bul</div>
      </Link>
      <nav className="flex items-center gap-6 text-base text-black">
        <Link to="/">Home</Link>
        <NavLink to="/register">Register</NavLink>
        <NavLink to="/login">Login</NavLink>
      </nav>
    </div>
  );
}
