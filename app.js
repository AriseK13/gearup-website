const express = require('express');
const admin = require('firebase-admin');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Firebase initialization
const serviceAccount = require('./config/gearup-df833-firebase-adminsdk-htilc-a7a47865bf.json');
admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  databaseURL: "https://gearup-df833.firebaseio.com"
});

const db = admin.firestore();

// Serve static files from the 'public' directory
app.use(express.static(path.join(__dirname, 'public')));

// Routes
app.get('/api/trending-products', async (req, res) => {
  try {
    const products = await getTrendingProducts();
    res.json(products);
  } catch (error) {
    console.error("Error fetching trending products:", error);
    res.status(500).send("Error fetching trending products");
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});

// EMA calculation and fetching trending products from Firestore
async function getTrendingProducts() {
  const ordersRef = db.collection('orders');
  const snapshot = await ordersRef.get();
  
  const productSales = {};

  // Collect sales data
  snapshot.forEach(doc => {
    const order = doc.data();
    const { items } = order;  // assuming 'items' is an array of product objects

    items.forEach(item => {
      if (!productSales[item.productId]) {
        productSales[item.productId] = { name: item.name, sales: [] };
      }
      productSales[item.productId].sales.push(item.quantity);
    });
  });

  const trendingProducts = [];
  const alpha = 0.1; // Smoothing factor for EMA (adjust as needed)

  // Calculate EMA for each product
  for (const productId in productSales) {
    const product = productSales[productId];
    const ema = calculateEMA(product.sales, alpha);
    trendingProducts.push({ productId, name: product.name, ema });
  }

  // Sort products by EMA score in descending order
  trendingProducts.sort((a, b) => b.ema - a.ema);

  // Return top trending products
  return trendingProducts.slice(0, 10); // Top 10 trending products
}

// Helper function to calculate EMA
function calculateEMA(sales, alpha) {
  let ema = sales[0];
  for (let i = 1; i < sales.length; i++) {
    ema = alpha * sales[i] + (1 - alpha) * ema;
  }
  return ema;
}
