package com.example.androidbooster.ui.splash

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.draw.drawWithCache
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/**
 * Android Booster SplashScreen - 2026 Ultra-Edition
 * 100% Layout Perfectie + Immersieve Effecten.
 */
@Composable
fun SplashScreen(
    modifier: Modifier = Modifier,
    appName: String = "ANDROID BOOSTER",
    tagline: String = "Boost • Clean • Optimize"
) {
    val infinite = rememberInfiniteTransition(label = "BoosterMain")

    // Custom Easing voor organische flow (Sinus-equivalent)
    val smoothEasing = CubicBezierEasing(0.445f, 0.05f, 0.55f, 0.95f)

    // Animatie-states voor de Mesh Background
    val meshShiftX by infinite.animateFloat(
        initialValue = -0.2f, targetValue = 0.2f,
        animationSpec = infiniteRepeatable(tween(8000, easing = LinearEasing), RepeatMode.Reverse),
        label = "MeshX"
    )
    val meshShiftY by infinite.animateFloat(
        initialValue = -0.1f, targetValue = 0.1f,
        animationSpec = infiniteRepeatable(tween(6000, easing = LinearEasing), RepeatMode.Reverse),
        label = "MeshY"
    )

    // Icon Dynamics
    val iconWobble by infinite.animateFloat(
        initialValue = -2f, targetValue = 2f,
        animationSpec = infiniteRepeatable(tween(1400, easing = smoothEasing), RepeatMode.Reverse),
        label = "IconWobble"
    )
    val pulse by infinite.animateFloat(
        initialValue = 0.85f, targetValue = 1.05f,
        animationSpec = infiniteRepeatable(tween(2500, easing = smoothEasing), RepeatMode.Reverse),
        label = "AuraPulse"
    )

    // Kleurenpalet: Midnight Mood Mode
    val coreDark = Color(0xFF071022)
    val deepNavy = Color(0xFF0B1B3A)
    val accentBlue = Color(0xFF5D7CFF)
    val glowColor = Color(0xFF9FB2FF)

    val density = LocalDensity.current

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(coreDark)
            .drawBehind {
                // 1. Layered Mesh Gradient Background
                drawRect(brush = Brush.verticalGradient(listOf(coreDark, deepNavy, coreDark)))

                drawCircle(
                    brush = Brush.radialGradient(
                        colors = listOf(accentBlue.copy(alpha = 0.12f), Color.Transparent),
                        center = Offset(size.width * (0.5f + meshShiftX), size.height * (0.3f + meshShiftY)),
                        radius = size.minDimension * 0.9f
                    )
                )
                drawCircle(
                    brush = Brush.radialGradient(
                        colors = listOf(Color(0xFF25E6C8).copy(alpha = 0.05f), Color.Transparent),
                        center = Offset(size.width * (0.3f - meshShiftX), size.height * (0.7f - meshShiftY)),
                        radius = size.minDimension * 0.7f
                    )
                )
            }
            .padding(horizontal = 32.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(35.dp)
        ) {
            // Icon met Schoonmaak-strepen
            Box(
                modifier = Modifier
                    .size(240.dp)
                    .drawWithCache {
                        val aura = Brush.radialGradient(
                            colors = listOf(glowColor.copy(alpha = 0.18f), Color.Transparent),
                            radius = size.minDimension * 0.65f
                        )
                        onDrawBehind {
                            drawCircle(brush = aura, radius = size.minDimension * 0.65f * pulse)
                        }
                    },
                contentAlignment = Alignment.Center
            ) {
                SqueegeeIcon(
                    modifier = Modifier.size(200.dp),
                    angleDeg = -35f + iconWobble,
                    lineColor = Color.White,
                    pulseAlpha = pulse
                )
            }

            // Typography Stack: Embossed Shadow Effect
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = appName,
                    style = MaterialTheme.typography.headlineLarge.copy(
                        fontWeight = FontWeight.Black,
                        letterSpacing = 3.5.sp,
                        fontSize = 34.sp,
                        shadow = Shadow(
                            color = accentBlue.copy(alpha = 0.5f),
                            offset = Offset(0f, with(density) { 2.dp.toPx() }),
                            blurRadius = with(density) { 5.dp.toPx() }
                        )
                    ),
                    color = Color.White
                )
                Spacer(Modifier.height(8.dp))
                Text(
                    text = tagline,
                    style = MaterialTheme.typography.bodyMedium.copy(
                        color = Color.White.copy(alpha = 0.60f),
                        letterSpacing = 1.2.sp,
                        fontWeight = FontWeight.SemiBold
                    ),
                    textAlign = TextAlign.Center
                )
            }

            Spacer(Modifier.height(15.dp))

            // Custom Glowing Progress Bar
            CustomGlowingProgressBar(
                modifier = Modifier
                    .fillMaxWidth(0.75f)
                    .height(8.dp),
                progressColor = Color.White,
                glowColor = accentBlue
            )
        }

        // Status melding met Fade-in animatie
        Text(
            text = "OPTIMIZING SYSTEM RESOURCES…",
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(bottom = 40.dp),
            style = MaterialTheme.typography.labelSmall.copy(
                color = Color.White.copy(alpha = 0.40f * pulse),
                fontWeight = FontWeight.Bold,
                letterSpacing = 2.sp
            )
        )
    }
}

@Composable
private fun CustomGlowingProgressBar(
    modifier: Modifier,
    progressColor: Color,
    glowColor: Color
) {
    val infinite = rememberInfiniteTransition(label = "ProgressAnim")
    val sweepPos by infinite.animateFloat(
        initialValue = 0f, targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(2000, easing = LinearEasing)),
        label = "Sweep"
    )

    Canvas(modifier = modifier.clip(RoundedCornerShape(100))) {
        val w = size.width
        val h = size.height

        // Track
        drawRoundRect(
            color = Color.White.copy(alpha = 0.1f),
            size = size,
            cornerRadius = CornerRadius(h / 2)
        )

        // Glowing "Plasma" Fill (statische 60% breedte met bewegende gradient)
        val fillWidth = w * 0.6f
        val brush = Brush.linearGradient(
            colors = listOf(
                progressColor.copy(alpha = 0.7f),
                progressColor,
                progressColor.copy(alpha = 0.7f)
            ),
            start = Offset(fillWidth * sweepPos - 100f, 0f),
            end = Offset(fillWidth * sweepPos + 100f, 0f),
            tileMode = TileMode.Mirror
        )

        drawRoundRect(
            brush = brush,
            size = Size(fillWidth, h),
            cornerRadius = CornerRadius(h / 2)
        )

        // Glow effect over de bar
        drawCircle(
            brush = Brush.radialGradient(
                colors = listOf(glowColor.copy(alpha = 0.4f), Color.Transparent),
                radius = 12.dp.toPx()
            ),
            center = Offset(fillWidth, h / 2)
        )
    }
}

@Composable
private fun SqueegeeIcon(
    modifier: Modifier,
    angleDeg: Float,
    lineColor: Color,
    pulseAlpha: Float
) {
    Canvas(modifier = modifier) {
        val w = size.width
        val h = size.height
        val stroke = w * 0.038f

        rotate(degrees = angleDeg, pivot = Offset(w * 0.5f, h * 0.45f)) {

            // Dynamische "Cleaning Streaks"
            fun streak(y: Float, start: Float, end: Float, alphaMult: Float) {
                drawLine(
                    color = lineColor.copy(alpha = 0.25f * alphaMult * pulseAlpha),
                    start = Offset(w * start, h * y),
                    end = Offset(w * end, h * y),
                    strokeWidth = stroke * 0.6f,
                    cap = StrokeCap.Round
                )
            }
            streak(0.25f, 0.2f, 0.8f, 1.0f)
            streak(0.40f, 0.15f, 0.6f, 0.7f)
            streak(0.55f, 0.3f, 0.5f, 0.5f)

            // Squeegee Head: Dual-layer Depth Effect
            val headW = w * 0.62f
            val headH = h * 0.15f
            val headX = (w - headW) / 2f
            val headY = h * 0.58f

            // Shadow/Depth layer
            drawRoundRect(
                color = lineColor.copy(alpha = 0.2f),
                topLeft = Offset(headX + 4.dp.toPx(), headY + 4.dp.toPx()),
                size = Size(headW, headH),
                cornerRadius = CornerRadius(6.dp.toPx()),
                style = Stroke(width = stroke)
            )

            // Active front layer
            drawRoundRect(
                color = lineColor,
                topLeft = Offset(headX, headY),
                size = Size(headW, headH),
                cornerRadius = CornerRadius(6.dp.toPx()),
                style = Stroke(width = stroke)
            )

            // Handle
            val handleX = headX + (headW * 0.58f)
            drawLine(
                color = lineColor,
                start = Offset(handleX, headY + headH),
                end = Offset(handleX, headY + headH + (h * 0.25f)),
                strokeWidth = stroke * 0.8f,
                cap = StrokeCap.Round
            )

            // Branded Sparkles
            drawCircle(color = lineColor, radius = 2.dp.toPx(), center = Offset(w * 0.85f, h * 0.25f))
            drawCircle(color = lineColor, radius = 1.dp.toPx(), center = Offset(w * 0.92f, h * 0.32f))
        }
    }
}
