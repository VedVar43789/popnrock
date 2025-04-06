import React from 'react';
import { useNavigate } from "react-router-dom";
import './NavigationButton.css';

const NavigationButton = ({ to, label }) => {
  const navigate = useNavigate();
  
  return (
    <button className="navigation-button" onClick={() => navigate("/livefeed")}>
      START!!!
    </button>
  );
};

export default NavigationButton;
