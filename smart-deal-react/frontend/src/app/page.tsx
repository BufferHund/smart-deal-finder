'use client'

import { Card, CardBody, CardFooter, Button } from "@heroui/react";
import { motion } from "framer-motion";
import Link from "next/link";
import Navbar from '../components/Navbar';

export default function Home() {
  return (
    <div className="min-h-screen relative overflow-hidden flex flex-col">
      <Navbar />

      {/* Abstract Background Orbs */}
      <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-purple-600/30 rounded-full blur-[120px]" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[600px] h-[600px] bg-pink-600/30 rounded-full blur-[120px]" />

      <main className="flex-grow flex items-center justify-center p-6 pt-24 z-10">
        <div className="max-w-6xl w-full grid lg:grid-cols-2 gap-12 items-center">

          {/* Text Section */}
          <div className="text-left space-y-6">
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
            >
              <h1 className="text-6xl md:text-7xl font-black text-white leading-tight">
                Shopping <br />
                <span className="bg-clip-text text-transparent bg-gradient-to-r from-pink-400 via-purple-400 to-indigo-400">
                  Reimagined
                </span>
              </h1>
            </motion.div>

            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="text-xl text-white/60 max-w-lg"
            >
              The AI-powered assistant that turns messy flyers into organized savings. Experience the future of deal finding today.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="flex gap-4 pt-4"
            >
              <Button
                as={Link}
                href="/shopper"
                size="lg"
                className="bg-white text-purple-900 font-bold shadow-xl hover:shadow-2xl hover:scale-105 transition-transform"
              >
                Start Shopping
              </Button>
              <Button
                as={Link}
                href="/admin"
                size="lg"
                variant="bordered"
                className="text-white border-white/30 hover:bg-white/10 font-semibold"
              >
                Admin Access
              </Button>
            </motion.div>
          </div>

          {/* Cards Section */}
          <div className="grid gap-6 perspective-1000">
            {/* Admin Feature Card */}
            <motion.div
              initial={{ opacity: 0, rotateY: 20, x: 50 }}
              animate={{ opacity: 1, rotateY: 0, x: 0 }}
              transition={{ delay: 0.3, type: "spring" }}
            >
              <Link href="/admin">
                <Card className="glass-card py-4 cursor-pointer group">
                  <CardBody className="flex flex-row items-center gap-6 p-6">
                    <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-3xl shadow-lg group-hover:scale-110 transition-transform">
                      📊
                    </div>
                    <div>
                      <h3 className="text-2xl font-bold text-white mb-1">Upload & Extract</h3>
                      <p className="text-white/60 text-sm">Convert paper flyers into digital data instantly with Gemini AI.</p>
                    </div>
                  </CardBody>
                </Card>
              </Link>
            </motion.div>

            {/* Shopper Feature Card */}
            <motion.div
              initial={{ opacity: 0, rotateY: 20, x: 50 }}
              animate={{ opacity: 1, rotateY: 0, x: 0 }}
              transition={{ delay: 0.5, type: "spring" }}
            >
              <Link href="/shopper">
                <Card className="glass-card py-4 cursor-pointer group">
                  <CardBody className="flex flex-row items-center gap-6 p-6">
                    <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-pink-500 to-orange-500 flex items-center justify-center text-3xl shadow-lg group-hover:scale-110 transition-transform">
                      🛍️
                    </div>
                    <div>
                      <h3 className="text-2xl font-bold text-white mb-1">Smart Shopping</h3>
                      <p className="text-white/60 text-sm">Personalized deals and AI Chef recipes at your fingertips.</p>
                    </div>
                  </CardBody>
                </Card>
              </Link>
            </motion.div>
          </div>

        </div>
      </main>

      <footer className="w-full p-6 text-center text-white/20 text-sm relative z-10">
        &copy; 2026 SmartDeal AI. Designed by Deepmind.
      </footer>
    </div>
  );
}
