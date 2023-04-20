// Demonstrates both async and non-async functions working fine
async function add({ x = 1, y = 1 }) {
  console.log(`Adding ${x} and ${y}`);
  return x + y;
}

async function subtract({ x = 1, y = 1 }) {
  console.log(`Subtracting ${x} and ${y}`);
  return x - y;
}

function multiply({ x = 1, y = 1 }) {
  console.log(`Multiplying ${x} and ${y}`);
  return x * y;
}

function divide({ x = 1, y = 1 }) {
  console.log(`Dividing ${x} and ${y}`);
  return x / y;
}

export { add, subtract, multiply, divide };
