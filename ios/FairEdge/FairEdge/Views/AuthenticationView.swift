//
//  AuthenticationView.swift
//  FairEdge
//
//  Created by Fair-Edge on 1/18/25.
//

import SwiftUI
import AuthenticationServices

/// Authentication view with Sign in with Apple and development login
struct AuthenticationView: View {
    @EnvironmentObject var authenticationService: AuthenticationService
    
    @State private var email = ""
    @State private var password = ""
    @State private var showingDevLogin = false
    
    var body: some View {
        VStack(spacing: 32) {
            // Logo and title
            headerSection
            
            // Sign in with Apple
            signInWithAppleSection
            
            // Development login (debug builds only)
            #if DEBUG
            developmentLoginSection
            #endif
            
            // Loading overlay
            if authenticationService.isLoading {
                loadingOverlay
            }
        }
        .padding()
        .alert("Authentication Error", isPresented: .constant(authenticationService.errorMessage != nil)) {
            Button("OK") {
                authenticationService.errorMessage = nil
            }
        } message: {
            if let errorMessage = authenticationService.errorMessage {
                Text(errorMessage)
            }
        }
    }
    
    // MARK: - Header Section
    
    private var headerSection: some View {
        VStack(spacing: 16) {
            Image(systemName: "chart.line.uptrend.xyaxis")
                .font(.system(size: 80))
                .foregroundColor(.blue)
            
            VStack(spacing: 8) {
                Text("Fair-Edge")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                
                Text("Sports Betting EV Analysis")
                    .font(.headline)
                    .foregroundColor(.secondary)
            }
            
            Text("Find the best betting opportunities with our expected value analysis")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
        }
    }
    
    // MARK: - Sign in with Apple Section
    
    private var signInWithAppleSection: some View {
        VStack(spacing: 16) {
            SignInWithAppleButton(
                onRequest: { request in
                    request.requestedScopes = [.email, .fullName]
                },
                onCompletion: { result in
                    // Handle result in AuthenticationService
                }
            )
            .signInWithAppleButtonStyle(.black)
            .frame(height: 50)
            .onTapGesture {
                authenticationService.signInWithApple()
            }
            
            Text("Secure authentication with your Apple ID")
                .font(.caption)
                .foregroundColor(.secondary)
        }
    }
    
    // MARK: - Development Login Section
    
    #if DEBUG
    private var developmentLoginSection: some View {
        VStack(spacing: 16) {
            Divider()
            
            Button("Development Login") {
                showingDevLogin.toggle()
            }
            .foregroundColor(.blue)
            .font(.footnote)
            
            if showingDevLogin {
                VStack(spacing: 12) {
                    TextField("Email", text: $email)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                        .keyboardType(.emailAddress)
                        .autocapitalization(.none)
                    
                    SecureField("Password", text: $password)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                    
                    Button("Sign In") {
                        authenticationService.signIn(email: email, password: password)
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(email.isEmpty || password.isEmpty || authenticationService.isLoading)
                }
                .padding()
                .background(Color(.systemGray6))
                .cornerRadius(12)
            }
        }
    }
    #endif
    
    // MARK: - Loading Overlay
    
    private var loadingOverlay: some View {
        ZStack {
            Color.black.opacity(0.3)
                .ignoresSafeArea()
            
            VStack(spacing: 16) {
                ProgressView()
                    .scaleEffect(1.5)
                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                
                Text("Signing in...")
                    .font(.headline)
                    .foregroundColor(.white)
            }
            .padding(32)
            .background(Color.black.opacity(0.8))
            .cornerRadius(16)
        }
    }
}

// MARK: - Preview

struct AuthenticationView_Previews: PreviewProvider {
    static var previews: some View {
        AuthenticationView()
            .environmentObject(AuthenticationService())
    }
}