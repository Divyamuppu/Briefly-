import React from 'react';
import '@/App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import SplashScreen from './pages/SplashScreen';
import Landing from './pages/Landing';
import CreateProject from './pages/CreateProject';
import VideoTypeSelection from './pages/VideoTypeSelection';
import SwipeInterface from './pages/SwipeInterface';
import BriefDashboard from './pages/BriefDashboard';
import { Toaster } from '@/components/ui/sonner';

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<SplashScreen />} />
          <Route path="/home" element={<Landing />} />
          <Route path="/create" element={<CreateProject />} />
          <Route path="/video-type" element={<VideoTypeSelection />} />
          <Route path="/swipe/:projectId" element={<SwipeInterface />} />
          <Route path="/brief/:projectId" element={<BriefDashboard />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-center" />
    </div>
  );
}

export default App;