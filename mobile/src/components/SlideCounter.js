import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

export default function SlideCounter({ value, onChange }) {
  const decrement = () => onChange(Math.max(2, value - 1));
  const increment = () => onChange(Math.min(12, value + 1));

  return (
    <View style={styles.container}>
      <Text style={styles.label}>Slides</Text>
      <View style={styles.controls}>
        <TouchableOpacity
          style={[styles.btn, value <= 2 && styles.btnDisabled]}
          onPress={decrement}
          disabled={value <= 2}
        >
          <Text style={styles.btnText}>−</Text>
        </TouchableOpacity>
        <Text style={styles.value}>{value}</Text>
        <TouchableOpacity
          style={[styles.btn, value >= 12 && styles.btnDisabled]}
          onPress={increment}
          disabled={value >= 12}
        >
          <Text style={styles.btnText}>+</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  label: {
    fontSize: 15,
    color: '#374151',
    fontWeight: '500',
  },
  controls: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  btn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#4F46E5',
    alignItems: 'center',
    justifyContent: 'center',
  },
  btnDisabled: {
    backgroundColor: '#E5E7EB',
  },
  btnText: {
    color: '#fff',
    fontSize: 20,
    lineHeight: 22,
    fontWeight: '600',
  },
  value: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    minWidth: 24,
    textAlign: 'center',
  },
});
