/**
 * A-GROSS SOS – React Native Mobile App
 * 
 * Setup:
 *   npx react-native init A_GROSS_SOS_RN
 *   cd A_GROSS_SOS_RN
 *   npm install @react-native-async-storage/async-storage react-native-sqlite-storage
 *   npm install react-native-vector-icons react-native-chart-kit
 * 
 * Spuštění:
 *   Android: npm run android
 *   iOS: npm run ios
 */

import React, { useState, useEffect } from 'react';
import {
  SafeAreaView,
  ScrollView,
  View,
  Text,
  TouchableOpacity,
  TextInput,
  FlatList,
  StyleSheet,
  Alert,
  ActivityIndicator,
  StatusBar,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { LineChart, BarChart } from 'react-native-chart-kit';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

// ═════════════════════════════════════════════════════════════════════
// STYLES
// ═════════════════════════════════════════════════════════════════════

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  header: {
    backgroundColor: '#1A1A1A',
    paddingTop: 10,
    paddingBottom: 15,
    paddingHorizontal: 15,
  },
  headerTitle: {
    color: '#FFF',
    fontSize: 20,
    fontWeight: '700',
  },
  headerSubtitle: {
    color: '#AAA',
    fontSize: 12,
    marginTop: 4,
  },
  nav: {
    flexDirection: 'row',
    backgroundColor: '#FFF',
    paddingVertical: 8,
    marginTop: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#EEE',
  },
  navButton: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderBottomWidth: 3,
    borderBottomColor: 'transparent',
  },
  navButtonActive: {
    borderBottomColor: '#1A1A1A',
  },
  navButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
  },
  navButtonTextActive: {
    color: '#1A1A1A',
  },
  content: {
    flex: 1,
    padding: 15,
  },
  card: {
    backgroundColor: '#FFF',
    borderRadius: 8,
    padding: 15,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 10,
    color: '#1A1A1A',
  },
  kpiRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 15,
  },
  kpiBox: {
    flex: 1,
    alignItems: 'center',
    paddingHorizontal: 5,
  },
  kpiLabel: {
    fontSize: 11,
    color: '#999',
    fontWeight: '600',
    marginBottom: 5,
    textTransform: 'uppercase',
  },
  kpiValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1A1A1A',
  },
  productItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 10,
    marginBottom: 8,
    backgroundColor: '#F9F9F9',
    borderRadius: 6,
    borderLeftWidth: 3,
    borderLeftColor: '#E8533A',
  },
  productInfo: {
    flex: 1,
    marginHorizontal: 10,
  },
  productName: {
    fontSize: 13,
    fontWeight: '600',
    color: '#1A1A1A',
  },
  productPrice: {
    fontSize: 11,
    color: '#666',
    marginTop: 2,
  },
  productMargin: {
    fontSize: 12,
    fontWeight: '700',
    color: '#2A7A4A',
  },
  button: {
    backgroundColor: '#1A1A1A',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 6,
    alignItems: 'center',
    marginTop: 10,
  },
  buttonText: {
    color: '#FFF',
    fontWeight: '600',
    fontSize: 14,
  },
  cartBadge: {
    position: 'absolute',
    top: -8,
    right: -8,
    backgroundColor: '#E8533A',
    borderRadius: 10,
    width: 20,
    height: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cartBadgeText: {
    color: '#FFF',
    fontSize: 10,
    fontWeight: '700',
  },
  input: {
    borderWidth: 1,
    borderColor: '#DDD',
    borderRadius: 6,
    padding: 10,
    marginBottom: 10,
    fontSize: 14,
    backgroundColor: '#FFF',
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1A1A1A',
    marginBottom: 10,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    alignSelf: 'flex-start',
  },
  badgeActive: {
    backgroundColor: '#E8F5EE',
  },
  badgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#2A7A4A',
  },
  loader: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  offlineIndicator: {
    backgroundColor: '#FFF3E0',
    padding: 8,
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 15,
    marginTop: 10,
    borderRadius: 4,
    borderLeftWidth: 3,
    borderLeftColor: '#C05000',
  },
  offlineIndicatorText: {
    marginLeft: 10,
    color: '#C05000',
    fontSize: 12,
    fontWeight: '600',
  },
});

// ═════════════════════════════════════════════════════════════════════
// MAIN APP
// ═════════════════════════════════════════════════════════════════════

const App = () => {
  const [activeTab, setActiveTab] = useState('home');
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [store, setStore] = useState(null);
  const [storeName, setStoreName] = useState('');
  const [isOnline, setIsOnline] = useState(true);
  const [loading, setLoading] = useState(false);

  // Inicializace
  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      setLoading(true);

      // Načíst uložené produkty
      const savedProducts = await AsyncStorage.getItem('products');
      if (savedProducts) {
        setProducts(JSON.parse(savedProducts));
      }

      // Načíst uložené obchody
      const savedStore = await AsyncStorage.getItem('storeId');
      if (savedStore) {
        setStore(JSON.parse(savedStore));
      }

      // Načíst nákupní košík
      const savedCart = await AsyncStorage.getItem('cart');
      if (savedCart) {
        setCart(JSON.parse(savedCart));
      }

      // Pokusit se synchronizovat
      await syncCatalog();
    } catch (error) {
      console.error('Init error:', error);
    } finally {
      setLoading(false);
    }
  };

  const syncCatalog = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/catalogs/sync', {
        timeout: 5000,
      });
      const data = await response.json();
      setProducts(data.products || []);
      await AsyncStorage.setItem('products', JSON.stringify(data.products));
      setIsOnline(true);
    } catch (error) {
      console.log('Offline mode - using cached catalog');
      setIsOnline(false);
    }
  };

  const registerStore = async () => {
    if (!storeName.trim()) {
      Alert.alert('Chyba', 'Zadej jméno obchodu');
      return;
    }

    try {
      const storeData = {
        id: Math.random().toString(),
        name: storeName,
        chain: 'Vietnamský obchod',
        registeredAt: new Date().toISOString(),
      };

      await AsyncStorage.setItem('storeId', JSON.stringify(storeData));
      setStore(storeData);
      setStoreName('');
      Alert.alert('✓ Obchod zaregistrován', storeName);
    } catch (error) {
      Alert.alert('Chyba', error.message);
    }
  };

  const addToCart = (product) => {
    const existing = cart.find(item => item.kod === product.kod);
    if (existing) {
      const updated = cart.map(item =>
        item.kod === product.kod
          ? { ...item, qty: item.qty + 1 }
          : item
      );
      setCart(updated);
    } else {
      setCart([...cart, { ...product, qty: 1 }]);
    }
    AsyncStorage.setItem('cart', JSON.stringify(cart));
  };

  const removeFromCart = (kod) => {
    setCart(cart.filter(item => item.kod !== kod));
  };

  const submitOrder = async () => {
    if (!store) {
      Alert.alert('Chyba', 'Nejdřív registruj obchod');
      return;
    }

    if (cart.length === 0) {
      Alert.alert('Chyba', 'Košík je prázdný');
      return;
    }

    try {
      const order = {
        id: `order-${Date.now()}`,
        storeId: store.id,
        storeName: store.name,
        items: cart,
        nc: cart.reduce((sum, item) => sum + (item.nc * item.qty), 0),
        marze: cart.reduce((sum, item) => sum + ((item.moc - item.nc) * item.qty), 0),
        moc: cart.reduce((sum, item) => sum + (item.moc * item.qty), 0),
        date: new Date().toISOString(),
        status: isOnline ? 'sent' : 'pending',
      };

      // Uložit lokálně
      const orders = JSON.parse(await AsyncStorage.getItem('orders') || '[]');
      orders.push(order);
      await AsyncStorage.setItem('orders', JSON.stringify(orders));

      // Pokusit se odeslat na server
      if (isOnline) {
        try {
          await fetch('http://localhost:5000/api/orders/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(order),
          });
        } catch (e) {
          console.log('Server offline, objednávka uložena lokálně');
        }
      }

      setCart([]);
      Alert.alert('✓ Objednávka odeslána', `ID: ${order.id}`);
    } catch (error) {
      Alert.alert('Chyba', error.message);
    }
  };

  const calculateTotals = () => {
    return {
      items: cart.length,
      nc: cart.reduce((sum, item) => sum + (item.nc * item.qty), 0),
      marze: cart.reduce((sum, item) => sum + ((item.moc - item.nc) * item.qty), 0),
    };
  };

  const totals = calculateTotals();

  // ─────────────────────────────────────────────────────────────────
  // RENDER HOME
  // ─────────────────────────────────────────────────────────────────

  const renderHome = () => (
    <ScrollView style={styles.content}>
      {!store ? (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>📝 Registrace obchodu</Text>
          <TextInput
            style={styles.input}
            placeholder="Jméno obchodu"
            value={storeName}
            onChangeText={setStoreName}
          />
          <TouchableOpacity
            style={styles.button}
            onPress={registerStore}
          >
            <Text style={styles.buttonText}>Registrovat obchod</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>🏪 {store.name}</Text>
          <Text style={styles.productPrice}>Zaregistrováno: {new Date(store.registeredAt).toLocaleDateString('cs-CZ')}</Text>
        </View>
      )}

      <View style={styles.card}>
        <View style={styles.kpiRow}>
          <View style={styles.kpiBox}>
            <Text style={styles.kpiLabel}>Nákup Kč</Text>
            <Text style={styles.kpiValue}>{totals.nc.toFixed(0)}</Text>
          </View>
          <View style={styles.kpiBox}>
            <Text style={styles.kpiLabel}>Marže Kč</Text>
            <Text style={styles.kpiValue} style={{ color: '#2A7A4A' }}>
              {totals.marze.toFixed(0)}
            </Text>
          </View>
          <View style={styles.kpiBox}>
            <Text style={styles.kpiLabel}>Položky</Text>
            <Text style={styles.kpiValue}>{totals.items}</Text>
          </View>
        </View>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>📊 Trend nákupů</Text>
        <LineChart
          data={{
            labels: ['Po', 'Út', 'St', 'Čt', 'Pá', 'So', 'Ne'],
            datasets: [{ data: [5, 8, 12, 15, 10, 18, 14] }],
          }}
          width={350}
          height={200}
          chartConfig={{
            backgroundColor: '#FFF',
            backgroundGradientFrom: '#FFF',
            backgroundGradientTo: '#FFF',
            color: () => '#1A1A1A',
            strokeWidth: 2,
          }}
          bezier
          style={{ marginLeft: -15 }}
        />
      </View>

      <TouchableOpacity
        style={styles.button}
        onPress={syncCatalog}
      >
        <Text style={styles.buttonText}>🔄 Synchronizovat katalog</Text>
      </TouchableOpacity>
    </ScrollView>
  );

  // ─────────────────────────────────────────────────────────────────
  // RENDER PRODUCTS
  // ─────────────────────────────────────────────────────────────────

  const renderProducts = () => (
    <ScrollView style={styles.content}>
      {!isOnline && (
        <View style={styles.offlineIndicator}>
          <Icon name="wifi-off" size={16} color="#C05000" />
          <Text style={styles.offlineIndicatorText}>Offline – používám uložený katalog</Text>
        </View>
      )}

      <View style={styles.card}>
        <Text style={styles.cardTitle}>📦 {products.length} Produktů</Text>
      </View>

      {products.slice(0, 20).map((product) => (
        <TouchableOpacity
          key={product.kod}
          style={styles.productItem}
          onPress={() => addToCart(product)}
        >
          <Icon name="package" size={20} color="#E8533A" />
          <View style={styles.productInfo}>
            <Text style={styles.productName}>{product.nazev}</Text>
            <Text style={styles.productPrice}>
              NC: {product.nc.toFixed(2)} Kč | MOC: {product.moc.toFixed(2)} Kč
            </Text>
            <Text style={styles.productMargin}>
              Marže: {(product.moc - product.nc).toFixed(2)} Kč
            </Text>
          </View>
          <Icon name="plus-circle" size={24} color="#1A1A1A" />
        </TouchableOpacity>
      ))}
    </ScrollView>
  );

  // ─────────────────────────────────────────────────────────────────
  // RENDER CART
  // ─────────────────────────────────────────────────────────────────

  const renderCart = () => (
    <ScrollView style={styles.content}>
      {cart.length === 0 ? (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>🛒 Nákupní košík</Text>
          <Text style={styles.productPrice}>Košík je prázdný</Text>
        </View>
      ) : (
        <>
          {cart.map((item) => (
            <View key={item.kod} style={styles.productItem}>
              <View style={styles.productInfo}>
                <Text style={styles.productName}>{item.nazev}</Text>
                <Text style={styles.productPrice}>
                  {item.qty} × {item.nc.toFixed(2)} = {(item.qty * item.nc).toFixed(2)} Kč
                </Text>
                <Text style={styles.productMargin}>
                  Marže: {((item.moc - item.nc) * item.qty).toFixed(2)} Kč
                </Text>
              </View>
              <TouchableOpacity onPress={() => removeFromCart(item.kod)}>
                <Icon name="trash-can" size={20} color="#E8533A" />
              </TouchableOpacity>
            </View>
          ))}

          <View style={styles.card}>
            <View style={styles.kpiRow}>
              <View style={styles.kpiBox}>
                <Text style={styles.kpiLabel}>Nákup</Text>
                <Text style={styles.kpiValue}>{totals.nc.toFixed(0)} Kč</Text>
              </View>
              <View style={styles.kpiBox}>
                <Text style={styles.kpiLabel}>Marže</Text>
                <Text style={styles.kpiValue} style={{ color: '#2A7A4A' }}>
                  {totals.marze.toFixed(0)} Kč
                </Text>
              </View>
              <View style={styles.kpiBox}>
                <Text style={styles.kpiLabel}>Prodej</Text>
                <Text style={styles.kpiValue}>{(totals.nc + totals.marze).toFixed(0)} Kč</Text>
              </View>
            </View>
          </View>

          <TouchableOpacity
            style={[styles.button, { backgroundColor: '#2A7A4A' }]}
            onPress={submitOrder}
          >
            <Text style={styles.buttonText}>✓ Odeslat objednávku</Text>
          </TouchableOpacity>
        </>
      )}
    </ScrollView>
  );

  // ─────────────────────────────────────────────────────────────────
  // RENDER HISTORY
  // ─────────────────────────────────────────────────────────────────

  const [history, setHistory] = useState([]);

  useEffect(() => {
    const loadHistory = async () => {
      const orders = JSON.parse(await AsyncStorage.getItem('orders') || '[]');
      setHistory(orders.slice(-5).reverse());
    };
    if (activeTab === 'history') loadHistory();
  }, [activeTab]);

  const renderHistory = () => (
    <ScrollView style={styles.content}>
      {history.length === 0 ? (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>📋 Lísty objednávek</Text>
          <Text style={styles.productPrice}>Žádné objednávky</Text>
        </View>
      ) : (
        history.map((order) => (
          <View key={order.id} style={styles.card}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
              <View>
                <Text style={styles.cardTitle}>{order.id}</Text>
                <Text style={styles.productPrice}>
                  {new Date(order.date).toLocaleDateString('cs-CZ')}
                </Text>
              </View>
              <View style={[styles.badge, styles.badgeActive]}>
                <Text style={styles.badgeText}>
                  {order.status === 'sent' ? 'Odeslána' : 'Čeká'}
                </Text>
              </View>
            </View>
            <View style={{ marginTop: 10, flexDirection: 'row', justifyContent: 'space-between' }}>
              <Text style={styles.productPrice}>Nákup: {order.nc.toFixed(0)} Kč</Text>
              <Text style={styles.productMargin}>Marže: {order.marze.toFixed(0)} Kč</Text>
            </View>
          </View>
        ))
      )}
    </ScrollView>
  );

  // ═════════════════════════════════════════════════════════════════════
  // MAIN RENDER
  // ═════════════════════════════════════════════════════════════════════

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loader}>
          <ActivityIndicator size="large" color="#1A1A1A" />
          <Text style={{ marginTop: 10, color: '#666' }}>Načítám aplikaci...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar backgroundColor="#1A1A1A" barStyle="light-content" />

      <View style={styles.header}>
        <Text style={styles.headerTitle}>🎯 A-GROSS SOS</Text>
        <Text style={styles.headerSubtitle}>
          {isOnline ? '🟢 Online' : '🔴 Offline'}
        </Text>
      </View>

      <View style={styles.nav}>
        {['home', 'products', 'cart', 'history'].map((tab) => (
          <TouchableOpacity
            key={tab}
            style={[
              styles.navButton,
              activeTab === tab && styles.navButtonActive,
            ]}
            onPress={() => setActiveTab(tab)}
          >
            <Text
              style={[
                styles.navButtonText,
                activeTab === tab && styles.navButtonTextActive,
              ]}
            >
              {tab === 'home' && '📊 Home'}
              {tab === 'products' && '📦 Produkty'}
              {tab === 'cart' && '🛒 Košík'}
              {tab === 'history' && '📋 Historie'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {activeTab === 'home' && renderHome()}
      {activeTab === 'products' && renderProducts()}
      {activeTab === 'cart' && renderCart()}
      {activeTab === 'history' && renderHistory()}
    </SafeAreaView>
  );
};

export default App;
