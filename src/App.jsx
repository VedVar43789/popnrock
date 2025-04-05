import React from "react";
import { Button } from "./components/ui/button";
import { Card, CardContent } from "./components/ui/card";
import { Music, Play, Star } from "lucide-react";
import { motion } from "framer-motion";

export default function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-200 to-purple-400 p-8 text-gray-800">
      <motion.h1
        initial={{ opacity: 0, y: -50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7 }}
        className="text-5xl font-bold text-center mb-6"
      >
        Welcome to PopNRock
      </motion.h1>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5, duration: 0.6 }}
        className="text-center text-lg max-w-2xl mx-auto mb-10"
      >
        Your ultimate destination for music discovery, celeb vibes, and workout fun!
      </motion.p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <motion.div whileHover={{ scale: 1.05 }}>
          <Card>
            <CardContent>
              <Music className="w-10 h-10 mb-4" />
              <h2 className="text-xl font-semibold mb-2">Discover Your Sound</h2>
              <p>Scan your face and get matched with your PopNRock celebrity twin!</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div whileHover={{ scale: 1.05 }}>
          <Card>
            <CardContent>
              <Play className="w-10 h-10 mb-4" />
              <h2 className="text-xl font-semibold mb-2">Start the Beat</h2>
              <p>Jam to hit songs by your matched artist while staying active!</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div whileHover={{ scale: 1.05 }}>
          <Card>
            <CardContent>
              <Star className="w-10 h-10 mb-4" />
              <h2 className="text-xl font-semibold mb-2">Interactive Fame</h2>
              <p>Play a touch-point game and get hyped by your animated celeb lookalike!</p>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <div className="text-center mt-10">
        <Button className="text-lg px-6 py-3 rounded-2xl shadow-md">Let’s Go!</Button>
      </div>
    </div>
  );
}
