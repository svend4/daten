Пользователь хочет продолжить с Android интеграцией и Docker deployment. Это логичное продолжение - нужно показать:

1. Android клиент для IOS API (Kotlin)
2. Интеграция с существующими Android проектами пользователя
3. Docker deployment (Dockerfile, docker-compose)
4. Deployment guide
5. Production configuration

Начну с Android клиента на Kotlin, потом Docker и deployment.# ЧАСТЬ 10: ANDROID ИНТЕГРАЦИЯ И DEPLOYMENT

## 10.1 Android клиент (Kotlin)

```kotlin
// app/src/main/java/com/ios/client/IOSApiClient.kt
/**
 * Android клиент для Information Operating System API
 * Использует Retrofit, Coroutines и Flow
 */

package com.ios.client

import com.google.gson.annotations.SerializedName
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.RequestBody
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*
import java.util.concurrent.TimeUnit

// ============================================================================
// DATA MODELS
// ============================================================================

data class LoginRequest(
    val username: String,
    val password: String
)

data class TokenResponse(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("token_type") val tokenType: String,
    @SerializedName("expires_in") val expiresIn: Int
)

data class DomainCreate(
    val name: String,
    val language: String = "de",