import React, { useState, useEffect } from "react";

// Basic TypeScript Examples
// Define a type for a user
type User = {
  id: number;
  name: string;
  isActive: boolean;
};

// Function to greet a user
const greetUser = (user: User): string => {
  return `Hello, ${user.name}! Your ID is ${user.id} and your account is ${
    user.isActive ? "active" : "inactive"
  }.`;
};

// Component to test TypeScript basics
const Test: React.FC = () => {
  const user: User = {
    id: 1,
    name: "John Doe",
    isActive: true,
  };

  const [count, setCount] = useState(0);

  useEffect(() => {
    console.log(`Component mounted. Current count: ${count}`);
  }, []);

  useEffect(() => {
    console.log(`Count changed to: ${count}`);
  }, [count]);

  return (
    <div>
      <h1>TypeScript Basics Test</h1>
      <p>{greetUser(user)}</p>
      <p>Current count: {count}</p>
      <button onClick={() => setCount(count + 1)}>Increase Count</button>
    </div>
  );
};

export default Test;
