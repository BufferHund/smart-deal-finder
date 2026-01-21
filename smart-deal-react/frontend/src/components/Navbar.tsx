'use client';

import {
    Navbar as HeroNavbar,
    NavbarBrand,
    NavbarContent,
    NavbarItem,
    NavbarMenuToggle,
    NavbarMenu,
    NavbarMenuItem,
    Link,
    Button,
} from "@heroui/react";
import { usePathname } from 'next/navigation';
import { useState } from "react";

export default function Navbar() {
    const pathname = usePathname();
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    return (
        <HeroNavbar
            shouldHideOnScroll
            className="bg-transparent backdrop-blur-md border-b border-white/10 fixed top-0 w-full z-50"
            maxWidth="xl"
            onMenuOpenChange={setIsMenuOpen}
        >
            <NavbarContent>
                <NavbarMenuToggle
                    aria-label={isMenuOpen ? "Close menu" : "Open menu"}
                    className="sm:hidden text-white"
                />
                <NavbarBrand>
                    <Link href="/" className="font-bold text-inherit hover:opacity-80 transition-opacity">
                        <span className="text-3xl mr-2 filter drop-shadow-lg">🏷️</span>
                        <span className="text-2xl tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-pink-500 to-violet-500 font-extrabold">
                            SmartDeal
                        </span>
                    </Link>
                </NavbarBrand>
            </NavbarContent>
            <NavbarContent className="hidden sm:flex gap-8" justify="center">
                <NavbarItem isActive={pathname === '/admin'}>
                    <Link
                        className={`text-lg transition-colors ${pathname === '/admin' ? 'text-pink-500 font-bold' : 'text-white/70 hover:text-white'}`}
                        href="/admin"
                    >
                        Admin Hub
                    </Link>
                </NavbarItem>
                <NavbarItem isActive={pathname === '/shopper'}>
                    <Link
                        className={`text-lg transition-colors ${pathname === '/shopper' ? 'text-violet-500 font-bold' : 'text-white/70 hover:text-white'}`}
                        href="/shopper"
                    >
                        Shopper Zone
                    </Link>
                </NavbarItem>
            </NavbarContent>
            <NavbarContent justify="end">
                <NavbarItem>
                    <Button
                        as={Link}
                        href="#"
                        variant="shadow"
                        className="bg-gradient-to-r from-pink-500 to-violet-600 text-white font-bold border border-white/20"
                    >
                        Sign In
                    </Button>
                </NavbarItem>
            </NavbarContent>

            <NavbarMenu className="bg-black/90 pt-10 backdrop-blur-xl">
                <NavbarMenuItem>
                    <Link
                        className="w-full text-2xl font-bold py-4 text-pink-500"
                        href="/admin"
                        size="lg"
                    >
                        Admin Hub
                    </Link>
                </NavbarMenuItem>
                <NavbarMenuItem>
                    <Link
                        className="w-full text-2xl font-bold py-4 text-violet-500"
                        href="/shopper"
                        size="lg"
                    >
                        Shopper Zone
                    </Link>
                </NavbarMenuItem>
            </NavbarMenu>
        </HeroNavbar>
    );
}
