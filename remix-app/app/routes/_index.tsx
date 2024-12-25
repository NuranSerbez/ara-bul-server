import type { MetaFunction } from "@remix-run/node";
import { useState } from "react";
import SearchInterface from "~/components/search-interface";

export const meta: MetaFunction = () => {
  return [
    { title: "Ara-Bul" },
    { name: "description", content: "Welcome to Remix!" },
  ];
};

export default function Index() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex-shrink-0">
              <h1 className="text-2xl font-bold text-gray-900">Ara-Bul</h1>
            </div>
            <div className="flex items-center">
              <a
                href="/login"
                className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              >
                Login
              </a>
              <a
                href="/register"
                className="ml-4 px-4 py-2 rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
              >
                Register
              </a>
            </div>
          </div>
        </div>
      </nav>

      <main>
        <SearchInterface />
      </main>

      <footer className="bg-white mt-auto">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
          <p className="text-center text-gray-500 text-sm">
            © 2024 Ara-Bul. Nuran Serbez.
          </p>
        </div>
      </footer>
    </div>
  );
}