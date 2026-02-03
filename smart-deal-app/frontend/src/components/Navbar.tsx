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
    Dropdown,
    DropdownTrigger,
    DropdownMenu,
    DropdownItem,
    Avatar,
} from "@heroui/react";
import { usePathname, useRouter } from 'next/navigation';
import { useState } from "react";
import { Tags, LogOut, User } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

export default function Navbar() {
    const pathname = usePathname();
    const router = useRouter();
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const { user, logout } = useAuth();

    const handleLogout = () => {
        logout();
        router.push('/login');
    };

    return (
        <HeroNavbar
            shouldHideOnScroll
            className="bg-white/80 dark:bg-transparent backdrop-blur-md border-b border-gray-200 dark:border-white/10 fixed top-0 w-full z-50"
            maxWidth="xl"
            onMenuOpenChange={setIsMenuOpen}
        >
            <NavbarContent>
                <NavbarMenuToggle
                    aria-label={isMenuOpen ? "Close menu" : "Open menu"}
                    className="sm:hidden text-gray-900 dark:text-white"
                />
                <NavbarBrand>
                    <Link href="/" className="font-bold text-inherit hover:opacity-80 transition-opacity flex items-center">
                        <Tags className="w-7 h-7 mr-2 text-indigo-500 dark:text-indigo-400" />
                        <span className="text-2xl tracking-tight text-foreground font-extrabold flex items-center">
                            SmartDeal
                        </span>
                    </Link>
                </NavbarBrand>
            </NavbarContent>
            <NavbarContent className="hidden sm:flex gap-8" justify="center">
                <NavbarItem isActive={pathname === '/admin'}>
                    <Link
                        className={`text-lg transition-colors ${pathname === '/admin' ? 'text-pink-500 font-bold' : 'text-gray-700 dark:text-white/70 hover:text-gray-900 dark:hover:text-white'}`}
                        href="/admin"
                    >
                        Admin Hub
                    </Link>
                </NavbarItem>
                <NavbarItem isActive={pathname === '/shopper'}>
                    <Link
                        className={`text-lg transition-colors ${pathname === '/shopper' ? 'text-violet-500 font-bold' : 'text-gray-700 dark:text-white/70 hover:text-gray-900 dark:hover:text-white'}`}
                        href="/shopper"
                    >
                        Shopper Zone
                    </Link>
                </NavbarItem>
            </NavbarContent>
            <NavbarContent justify="end">
                <NavbarItem>
                    {user ? (
                        <Dropdown placement="bottom-end">
                            <DropdownTrigger>
                                <Button
                                    variant="flat"
                                    className="gap-2 px-3"
                                >
                                    <Avatar
                                        name={user.email.charAt(0).toUpperCase()}
                                        size="sm"
                                        className="bg-gradient-to-r from-pink-500 to-violet-600 text-white"
                                    />
                                    <span className="hidden sm:inline text-sm font-medium text-foreground">
                                        {user.email.split('@')[0]}
                                    </span>
                                </Button>
                            </DropdownTrigger>
                            <DropdownMenu aria-label="User menu">
                                <DropdownItem key="email" className="text-sm text-gray-500" isReadOnly>
                                    {user.email}
                                </DropdownItem>
                                <DropdownItem
                                    key="logout"
                                    color="danger"
                                    startContent={<LogOut size={16} />}
                                    onPress={handleLogout}
                                >
                                    Logout
                                </DropdownItem>
                            </DropdownMenu>
                        </Dropdown>
                    ) : (
                        <Button
                            as={Link}
                            href="/login"
                            variant="shadow"
                            className="bg-gradient-to-r from-pink-500 to-violet-600 text-white font-bold border border-white/20"
                        >
                            Sign In
                        </Button>
                    )}
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
