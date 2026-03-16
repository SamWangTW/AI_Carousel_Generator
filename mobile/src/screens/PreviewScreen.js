import React, { useRef, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Image } from 'expo-image';
import * as MediaLibrary from 'expo-media-library';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const SLIDE_WIDTH = SCREEN_WIDTH - 48;
const BASE_URL = 'http://192.168.0.117:8000';

function QualityScore({ score }) {
  if (!score || score.overall === null) return null;
  const items = [
    { label: 'Hook', value: score.hook_strength },
    { label: 'Clarity', value: score.content_clarity },
    { label: 'CTA', value: score.cta_effectiveness },
  ];
  return (
    <View style={styles.scoreCard}>
      <Text style={styles.sectionLabel}>Quality Score</Text>
      <View style={styles.scoreRow}>
        {items.map(({ label, value }) => (
          <View key={label} style={styles.scoreItem}>
            <Text style={styles.scoreValue}>{value ?? '—'}</Text>
            <Text style={styles.scoreLabel}>{label}</Text>
          </View>
        ))}
        <View style={[styles.scoreItem, styles.scoreOverall]}>
          <Text style={[styles.scoreValue, styles.scoreOverallValue]}>
            {score.overall ?? '—'}
          </Text>
          <Text style={styles.scoreLabel}>Overall</Text>
        </View>
      </View>
    </View>
  );
}

export default function PreviewScreen({ route, navigation }) {
  const { result } = route.params;
  const {
    slides,
    caption,
    hashtags,
    quality_score,
    tone,
    tone_reason,
    slide_image_urls,
  } = result;

  const [activeIndex, setActiveIndex] = useState(0);
  const [exporting, setExporting] = useState(false);
  const scrollRef = useRef(null);

  const handleScroll = (e) => {
    const index = Math.round(e.nativeEvent.contentOffset.x / SLIDE_WIDTH);
    setActiveIndex(index);
  };

  const handleExport = async () => {
    const { status } = await MediaLibrary.requestPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission denied', 'Allow photo library access to save images.');
      return;
    }

    setExporting(true);
    try {
      let saved = 0;
      for (const url of slide_image_urls) {
        const fullUrl = `${BASE_URL}${url}`;
        // Download via fetch and save as file
        const response = await fetch(fullUrl);
        const blob = await response.blob();
        const reader = new FileReader();
        await new Promise((resolve, reject) => {
          reader.onloadend = resolve;
          reader.onerror = reject;
          reader.readAsDataURL(blob);
        });
        const base64 = reader.result;
        await MediaLibrary.createAssetAsync(base64);
        saved++;
      }
      Alert.alert('Saved!', `${saved} slide${saved !== 1 ? 's' : ''} saved to your camera roll.`);
    } catch (err) {
      Alert.alert('Export failed', err.message || 'Could not save images.');
    } finally {
      setExporting(false);
    }
  };

  const toneLabel = tone
    ? tone.charAt(0).toUpperCase() + tone.slice(1)
    : null;

  return (
    <SafeAreaView style={styles.safe} edges={['bottom']}>
      <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>

        {/* Slide carousel */}
        <ScrollView
          ref={scrollRef}
          horizontal
          pagingEnabled
          showsHorizontalScrollIndicator={false}
          onScroll={handleScroll}
          scrollEventThrottle={16}
          decelerationRate="fast"
          snapToInterval={SLIDE_WIDTH}
          contentContainerStyle={styles.carouselContent}
          style={styles.carousel}
        >
          {slide_image_urls.map((url, i) => (
            <View key={i} style={styles.slideWrapper}>
              <Image
                source={{ uri: `${BASE_URL}${url}` }}
                style={styles.slideImage}
                contentFit="contain"
                transition={200}
              />
            </View>
          ))}
        </ScrollView>

        {/* Pagination dots */}
        <View style={styles.dots}>
          {slide_image_urls.map((_, i) => (
            <View
              key={i}
              style={[styles.dot, i === activeIndex && styles.dotActive]}
            />
          ))}
        </View>

        {/* Slide counter */}
        <Text style={styles.slideCounter}>
          {activeIndex + 1} / {slide_image_urls.length}
        </Text>

        {/* Detected tone */}
        {toneLabel && (
          <View style={styles.toneBadge}>
            <Text style={styles.toneTitle}>Tone: {toneLabel}</Text>
            {tone_reason ? (
              <Text style={styles.toneReason}>{tone_reason}</Text>
            ) : null}
          </View>
        )}

        {/* Quality score */}
        <QualityScore score={quality_score} />

        {/* Caption */}
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>Caption</Text>
          <Text style={styles.captionText}>{caption}</Text>
        </View>

        {/* Hashtags */}
        {hashtags && hashtags.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionLabel}>Hashtags</Text>
            <View style={styles.hashtagRow}>
              {hashtags.map((tag, i) => (
                <View key={i} style={styles.hashtag}>
                  <Text style={styles.hashtagText}>{tag}</Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Export button */}
        <TouchableOpacity
          style={[styles.exportButton, exporting && styles.exportButtonDisabled]}
          onPress={handleExport}
          disabled={exporting}
          activeOpacity={0.85}
        >
          {exporting ? (
            <View style={styles.exportRow}>
              <ActivityIndicator color="#fff" size="small" />
              <Text style={styles.exportText}>Saving…</Text>
            </View>
          ) : (
            <Text style={styles.exportText}>Save to Camera Roll</Text>
          )}
        </TouchableOpacity>

        {/* Back button */}
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
          activeOpacity={0.7}
        >
          <Text style={styles.backText}>← Generate another</Text>
        </TouchableOpacity>

      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#fff' },
  container: {
    paddingBottom: 48,
  },

  // Carousel
  carousel: {
    marginTop: 16,
  },
  carouselContent: {
    paddingHorizontal: 24,
    gap: 0,
  },
  slideWrapper: {
    width: SLIDE_WIDTH,
    alignItems: 'center',
  },
  slideImage: {
    width: SLIDE_WIDTH,
    height: SLIDE_WIDTH * (1350 / 1080),
    borderRadius: 12,
    backgroundColor: '#F3F4F6',
  },

  // Dots
  dots: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 14,
    gap: 6,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#D1D5DB',
  },
  dotActive: {
    backgroundColor: '#4F46E5',
    width: 18,
  },
  slideCounter: {
    textAlign: 'center',
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 6,
    marginBottom: 20,
  },

  // Tone badge
  toneBadge: {
    marginHorizontal: 24,
    backgroundColor: '#EEF2FF',
    borderRadius: 10,
    padding: 14,
    marginBottom: 16,
  },
  toneTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#4F46E5',
    marginBottom: 4,
  },
  toneReason: {
    fontSize: 13,
    color: '#6366F1',
    lineHeight: 19,
  },

  // Quality score
  scoreCard: {
    marginHorizontal: 24,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  scoreRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 12,
  },
  scoreItem: {
    alignItems: 'center',
  },
  scoreOverall: {
    backgroundColor: '#F5F3FF',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  scoreValue: {
    fontSize: 24,
    fontWeight: '800',
    color: '#111827',
  },
  scoreOverallValue: {
    color: '#4F46E5',
  },
  scoreLabel: {
    fontSize: 11,
    color: '#9CA3AF',
    marginTop: 2,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },

  // Sections
  section: {
    marginHorizontal: 24,
    marginBottom: 16,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#9CA3AF',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  captionText: {
    fontSize: 15,
    color: '#374151',
    lineHeight: 23,
  },

  // Hashtags
  hashtagRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  hashtag: {
    backgroundColor: '#F3F4F6',
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  hashtagText: {
    fontSize: 13,
    color: '#4F46E5',
    fontWeight: '500',
  },

  // Buttons
  exportButton: {
    backgroundColor: '#4F46E5',
    borderRadius: 14,
    paddingVertical: 16,
    marginHorizontal: 24,
    alignItems: 'center',
    marginBottom: 12,
    marginTop: 8,
  },
  exportButtonDisabled: {
    backgroundColor: '#A5B4FC',
  },
  exportRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  exportText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
  },
  backButton: {
    alignItems: 'center',
    paddingVertical: 12,
  },
  backText: {
    fontSize: 14,
    color: '#6B7280',
  },
});
