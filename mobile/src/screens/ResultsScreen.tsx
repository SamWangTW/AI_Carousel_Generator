import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Dimensions,
  ActivityIndicator,
  NativeSyntheticEvent,
  NativeScrollEvent,
} from 'react-native';
import { Image } from 'expo-image';
import * as Sharing from 'expo-sharing';
import * as Clipboard from 'expo-clipboard';
import * as FileSystem from 'expo-file-system/legacy';
import { SafeAreaView } from 'react-native-safe-area-context';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const SLIDE_PADDING = 20;
const SLIDE_WIDTH = SCREEN_WIDTH - SLIDE_PADDING * 2;
const SLIDE_HEIGHT = SLIDE_WIDTH * (1350 / 1080);

const BASE_URL = 'http://192.168.0.117:8000';
const ACCENT = '#4F46E5';

// ── Types ──────────────────────────────────────────────────────────────────────

interface Slide {
  index: number;
  title: string;
  body: string;
}

interface CarouselResult {
  project_id: string;
  main_topic: string;
  tone: string;
  tone_reason: string | null;
  slides: Slide[];
  caption: string;
  hashtags: string[];
  cta: string;
  quality_score: {
    hook_strength: number | null;
    content_clarity: number | null;
    cta_effectiveness: number | null;
    overall: number | null;
  } | null;
  slide_image_urls: string[];
}

interface Props {
  route: { params: { result: CarouselResult } };
  navigation: { navigate: (screen: string) => void };
}

// ── Screen ─────────────────────────────────────────────────────────────────────

export default function ResultsScreen({ route, navigation }: Props) {
  const { result } = route.params;
  const { caption, hashtags, cta, slide_image_urls } = result;

  const fullImageUrls = slide_image_urls.map((url) => `${BASE_URL}${url}`);
  const total = fullImageUrls.length;

  const [activeIndex, setActiveIndex] = useState(0);
  const [sharing, setSharing] = useState(false);
  // Two-phase status: "Preparing 2 of 6…" → "Sharing 1 of 6…"
  const [shareStatus, setShareStatus] = useState('');
  const [captionCopied, setCaptionCopied] = useState(false);
  const [hashtagsCopied, setHashtagsCopied] = useState(false);

  // ── Carousel scroll tracking ──────────────────────────────────────────────

  const handleCarouselScroll = useCallback(
    (e: NativeSyntheticEvent<NativeScrollEvent>) => {
      const index = Math.round(e.nativeEvent.contentOffset.x / SCREEN_WIDTH);
      setActiveIndex(Math.max(0, Math.min(index, total - 1)));
    },
    [total],
  );

  // ── Share current slide ───────────────────────────────────────────────────

  const handleShare = useCallback(async () => {
    const isAvailable = await Sharing.isAvailableAsync();
    if (!isAvailable) {
      Alert.alert('Not Supported', 'Sharing is not available on this device.');
      return;
    }

    setSharing(true);
    setShareStatus('Preparing…');
    try {
      const dest = `${FileSystem.cacheDirectory}carousel_slide_${activeIndex + 1}.png`;
      const { status } = await FileSystem.downloadAsync(fullImageUrls[activeIndex], dest);
      if (status !== 200) throw new Error(`HTTP ${status}`);

      setShareStatus('Opening…');
      await Sharing.shareAsync(dest, {
        mimeType: 'image/png',
        dialogTitle: `Slide ${activeIndex + 1} of ${total}`,
        UTI: 'public.png',
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message.toLowerCase() : '';
      if (!msg.includes('cancel') && !msg.includes('dismiss')) {
        Alert.alert('Could not share slide', 'Please try again.');
      }
    } finally {
      setSharing(false);
      setShareStatus('');
    }
  }, [fullImageUrls, activeIndex, total]);

  // ── Copy helpers ──────────────────────────────────────────────────────────

  const handleCopyCaption = useCallback(async () => {
    const full = cta ? `${caption}\n\n${cta}` : caption;
    await Clipboard.setStringAsync(full);
    setCaptionCopied(true);
    setTimeout(() => setCaptionCopied(false), 2000);
  }, [caption, cta]);

  const handleCopyHashtags = useCallback(async () => {
    await Clipboard.setStringAsync(hashtags.join(' '));
    setHashtagsCopied(true);
    setTimeout(() => setHashtagsCopied(false), 2000);
  }, [hashtags]);

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <SafeAreaView style={styles.root} edges={['bottom']}>
      <ScrollView
        style={styles.scroll}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {/* ── Carousel preview ──────────────────────────────────────────── */}
        <View style={styles.carouselContainer}>
          <ScrollView
            horizontal
            pagingEnabled
            showsHorizontalScrollIndicator={false}
            onMomentumScrollEnd={handleCarouselScroll}
            decelerationRate="fast"
          >
            {fullImageUrls.map((url, i) => (
              <View key={i} style={styles.slideFrame}>
                <Image
                  source={{ uri: url }}
                  style={styles.slideImage}
                  contentFit="contain"
                />
              </View>
            ))}
          </ScrollView>

          {/* Pagination dots */}
          <View style={styles.dotsRow}>
            {fullImageUrls.map((_, i) => (
              <View
                key={i}
                style={[styles.dot, i === activeIndex && styles.dotActive]}
              />
            ))}
          </View>

          {/* Slide counter */}
          <Text style={styles.counter}>
            {activeIndex + 1} / {total}
          </Text>
        </View>

        {/* ── Share button ──────────────────────────────────────────────── */}
        <TouchableOpacity
          style={[styles.shareBtn, sharing && styles.shareBtnDisabled]}
          onPress={handleShare}
          disabled={sharing}
          activeOpacity={0.85}
        >
          {sharing ? (
            <View style={styles.shareProgress}>
              <ActivityIndicator color="#fff" size="small" />
              <Text style={styles.shareProgressText}>{shareStatus}</Text>
            </View>
          ) : (
            <Text style={styles.shareBtnText}>
              Share Slide {activeIndex + 1} of {total}
            </Text>
          )}
        </TouchableOpacity>

        {/* ── Caption ───────────────────────────────────────────────────── */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Caption</Text>
            <TouchableOpacity
              style={styles.copyBtn}
              onPress={handleCopyCaption}
              activeOpacity={0.7}
            >
              <Text style={styles.copyIcon}>{captionCopied ? '✅' : '📋'}</Text>
              <Text style={[styles.copyLabel, captionCopied && styles.copyLabelDone]}>
                {captionCopied ? 'Copied!' : 'Copy'}
              </Text>
            </TouchableOpacity>
          </View>
          <View style={styles.card}>
            <Text style={styles.captionText}>{caption}</Text>
            {cta ? <Text style={styles.ctaText}>{cta}</Text> : null}
          </View>
        </View>

        {/* ── Hashtags ──────────────────────────────────────────────────── */}
        <View style={[styles.section, styles.lastSection]}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Hashtags</Text>
            <TouchableOpacity
              style={styles.copyBtn}
              onPress={handleCopyHashtags}
              activeOpacity={0.7}
            >
              <Text style={styles.copyIcon}>{hashtagsCopied ? '✅' : '📋'}</Text>
              <Text style={[styles.copyLabel, hashtagsCopied && styles.copyLabelDone]}>
                {hashtagsCopied ? 'Copied!' : 'Copy'}
              </Text>
            </TouchableOpacity>
          </View>
          <View style={styles.card}>
            <View style={styles.tagWrap}>
              {hashtags.map((tag, i) => (
                <View key={i} style={styles.tag}>
                  <Text style={styles.tagText}>{tag}</Text>
                </View>
              ))}
            </View>
          </View>
        </View>

        {/* ── Generate another ──────────────────────────────────────────── */}
        <TouchableOpacity
          style={styles.secondaryBtn}
          onPress={() => navigation.navigate('Home')}
          activeOpacity={0.7}
        >
          <Text style={styles.secondaryBtnText}>Generate Another</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

// ── Styles ─────────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#F9FAFB' },
  scroll: { flex: 1 },
  scrollContent: { paddingBottom: 40 },

  // Carousel
  carouselContainer: {
    backgroundColor: '#111827',
    paddingTop: 20,
    paddingBottom: 16,
  },
  slideFrame: {
    width: SCREEN_WIDTH,
    alignItems: 'center',
    paddingHorizontal: SLIDE_PADDING,
  },
  slideImage: {
    width: SLIDE_WIDTH,
    height: SLIDE_HEIGHT,
    borderRadius: 12,
    backgroundColor: '#1F2937',
  },
  dotsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 14,
    gap: 6,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: 'rgba(255,255,255,0.3)',
  },
  dotActive: {
    width: 18,
    backgroundColor: '#fff',
  },
  counter: {
    textAlign: 'center',
    color: 'rgba(255,255,255,0.45)',
    fontSize: 12,
    marginTop: 8,
  },

  // Share button
  shareBtn: {
    marginHorizontal: 20,
    marginTop: 20,
    backgroundColor: ACCENT,
    paddingVertical: 15,
    borderRadius: 14,
    alignItems: 'center',
    minHeight: 52,
    justifyContent: 'center',
  },
  shareBtnDisabled: { opacity: 0.7 },
  shareBtnText: { color: '#fff', fontWeight: '700', fontSize: 16 },
  shareProgress: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  shareProgressText: { color: '#fff', fontSize: 14, fontWeight: '600' },

  // Sections
  section: { marginTop: 24, paddingHorizontal: 20 },
  lastSection: { marginBottom: 4 },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  sectionTitle: { fontSize: 16, fontWeight: '700', color: '#111827' },

  // Copy button
  copyBtn: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  copyIcon: { fontSize: 15 },
  copyLabel: { fontSize: 13, fontWeight: '600', color: '#6B7280' },
  copyLabelDone: { color: ACCENT },

  // Card
  card: {
    backgroundColor: '#fff',
    borderRadius: 14,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  captionText: { fontSize: 15, color: '#374151', lineHeight: 22 },
  ctaText: {
    marginTop: 10,
    fontSize: 14,
    fontWeight: '600',
    color: ACCENT,
  },

  // Hashtags
  tagWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  tag: {
    backgroundColor: '#EEF2FF',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 20,
  },
  tagText: { color: ACCENT, fontSize: 13, fontWeight: '600' },

  // Generate another
  secondaryBtn: {
    marginHorizontal: 20,
    marginTop: 20,
    paddingVertical: 15,
    borderRadius: 14,
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: '#E5E7EB',
    backgroundColor: '#fff',
  },
  secondaryBtnText: { color: '#374151', fontWeight: '600', fontSize: 15 },
});
