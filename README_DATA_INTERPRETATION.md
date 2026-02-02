# Quick Reference: Data Interpretation

## 🎯 TL;DR - Cosa Guardare

| Vuoi sapere... | Guarda... | NON guardare... |
|----------------|-----------|-----------------|
| **Produzione solare effettiva** | `sum(mpp.pdc)` | ❌ `total_pac` |
| **Energia verso casa** | `total_pac` | ✅ OK |
| **Batteria carica/scarica** | `bat_current` (±) | |
| **Dalla rete** | `metering_grid_w_in` | |
| **Verso rete** | `metering_grid_w_out` | |

---

## ⚠️ Errore Comune #1

```python
# ❌ SBAGLIATO
solar_production = data.total_pac  # NOOOO!
# Questo include anche batteria!

# ✅ CORRETTO
solar_production = sum(mpp.pdc for mpp in data.mpp.values())
```

---

## 📊 Interpretazione Rapida

### Se PDC = 0 ma PAC > 0
→ **L'energia viene dalla batteria o dalla rete, NON dal sole!**

### Se bat_current < 0
→ **Batteria in scarica** (fornisce energia)

### Se bat_current > 0
→ **Batteria in carica** (assorbe energia)

---

## 🔢 Conversioni Unità

```python
# Voltage: stored as V × 100
voltage_v = data.bat_voltage / 100.0

# Current: stored as mA
current_a = data.bat_current / 1000.0

# Power: stored as W
power_kw = data.total_pac / 1000.0

# Energy: stored as Wh
energy_kwh = data.e_total / 1000.0

# Frequency: stored as Hz × 100
freq_hz = data.grid_freq / 100.0

# Temperature: stored as °C × 100
temp_c = data.temperature / 100.0
```

---

## 📈 Monitoraggio Raccomandato

### Display Principale
1. **Solar Production** (PDC totale)
2. **Battery Power** (con direzione ±)
3. **Inverter Output** (PAC)
4. **Grid Balance** (import/export)

### Log/Database
- Salvare **PDC** e **PAC** separatamente
- Salvare direzione batteria
- Timestamp per analisi time-of-use

---

Per documentazione completa, vedi [ENERGY_FLOW.md](./ENERGY_FLOW.md)
