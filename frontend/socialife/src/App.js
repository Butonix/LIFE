import React, {Component} from 'react';
import './App.css'
import {BrowserRouter as Router, Route, Link} from 'react-router-dom'
import Login from './components/login'
import Signup from './components/signup'
import Home from './components/home'
import UserProfile from './components/userProfile'
import ChatRoom from './components/chatRoom'

function App() {
  return (
    <Router>
        <Route path="/login" exact component={Login} />
        <Route path="/signup" exact component={Signup} />
        <Route path="/" exact component={Home} />
        <Route path="/profile/:profileName" component={UserProfile} />
        <Route path="/chat/:uuid" component={ChatRoom} />
    </Router>
  );
}

export default App;
