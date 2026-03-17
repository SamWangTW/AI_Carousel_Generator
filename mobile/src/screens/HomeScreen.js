import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import SlideCounter from '../components/SlideCounter';
import { generateCarousel } from '../api/carousel';

export default function HomeScreen({ navigation }) {
  const [videoUrl, setVideoUrl] = useState('');
  const [slideCount, setSlideCount] = useState(6);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    const trimmed = videoUrl.trim();
    if (!trimmed) {
      Alert.alert('Missing URL', 'Please enter a YouTube video URL.');
      return;
    }

    setLoading(true);
    try {
      const result = await generateCarousel({ videoUrl: trimmed, slideCount });
      navigation.navigate('Results', { result });
    } catch (err) {
      Alert.alert('Error', err.message || 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          contentContainerStyle={styles.container}
          keyboardShouldPersistTaps="handled"
        >
          {/* Header */}
          <View style={styles.header}>
            <View style={styles.accentDot} />
            <Text style={styles.title}>Carousel Generator</Text>
            <Text style={styles.subtitle}>
              Turn any YouTube video into an Instagram carousel post.
            </Text>
          </View>

          {/* Form */}
          <View style={styles.form}>
            <Text style={styles.fieldLabel}>YouTube URL</Text>
            <TextInput
              style={styles.input}
              placeholder="https://www.youtube.com/watch?v=..."
              placeholderTextColor="#9CA3AF"
              value={videoUrl}
              onChangeText={setVideoUrl}
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="url"
              editable={!loading}
            />

            <Text style={[styles.fieldLabel, { marginTop: 16 }]}>Slide Count</Text>
            <SlideCounter value={slideCount} onChange={setSlideCount} />

            <View style={styles.autoToneBadge}>
              <Text style={styles.autoToneText}>
                ✦  Tone detected automatically by AI
              </Text>
            </View>
          </View>

          {/* Button */}
          <TouchableOpacity
            style={[styles.button, loading && styles.buttonDisabled]}
            onPress={handleGenerate}
            disabled={loading}
            activeOpacity={0.85}
          >
            {loading ? (
              <View style={styles.loadingRow}>
                <ActivityIndicator color="#fff" size="small" />
                <Text style={styles.loadingText}>Generating carousel…</Text>
              </View>
            ) : (
              <Text style={styles.buttonText}>Generate Carousel</Text>
            )}
          </TouchableOpacity>

          {loading && (
            <Text style={styles.loadingHint}>
              Fetching transcript, planning slides, and rendering images.{'\n'}This takes 1–3 minutes — please keep the app open.
            </Text>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#fff' },
  flex: { flex: 1 },
  container: {
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingTop: 32,
    paddingBottom: 40,
  },
  header: {
    marginBottom: 40,
  },
  accentDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#4F46E5',
    marginBottom: 12,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    color: '#111827',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 15,
    color: '#6B7280',
    lineHeight: 22,
  },
  form: {
    flex: 1,
  },
  fieldLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  input: {
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 15,
    color: '#111827',
  },
  autoToneBadge: {
    marginTop: 20,
    backgroundColor: '#EEF2FF',
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10,
    alignSelf: 'flex-start',
  },
  autoToneText: {
    fontSize: 13,
    color: '#4F46E5',
    fontWeight: '500',
  },
  button: {
    backgroundColor: '#4F46E5',
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 32,
  },
  buttonDisabled: {
    backgroundColor: '#A5B4FC',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
  },
  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  loadingText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '600',
  },
  loadingHint: {
    marginTop: 16,
    textAlign: 'center',
    fontSize: 13,
    color: '#9CA3AF',
    lineHeight: 20,
  },
});
