//
//  AuthenticationService.swift
//  FairEdge
//
//  Created by Fair-Edge on 1/18/25.
//

import Foundation
import Combine
import AuthenticationServices

/// Authentication service handling Sign in with Apple and mobile session management
class AuthenticationService: NSObject, ObservableObject {
    
    // MARK: - Published Properties
    
    @Published var isAuthenticated = false
    @Published var currentUser: User?
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    // MARK: - Private Properties
    
    private let apiService = APIService()
    private var cancellables = Set<AnyCancellable>()
    
    // MARK: - Initialization
    
    override init() {
        super.init()
        checkAuthenticationStatus()
    }
    
    // MARK: - Public Methods
    
    /// Check if user is currently authenticated
    func checkAuthenticationStatus() {
        guard KeychainService.shared.exists(for: "access_token") else {
            self.isAuthenticated = false
            self.currentUser = nil
            return
        }
        
        // Validate token by trying to refresh
        apiService.refreshToken()
            .receive(on: DispatchQueue.main)
            .sink(
                receiveCompletion: { [weak self] completion in
                    switch completion {
                    case .finished:
                        self?.isAuthenticated = true
                    case .failure:
                        self?.signOut()
                    }
                },
                receiveValue: { _ in }
            )
            .store(in: &cancellables)
    }
    
    /// Sign in with Apple ID
    func signInWithApple() {
        isLoading = true
        errorMessage = nil
        
        let request = ASAuthorizationAppleIDProvider().createRequest()
        request.requestedScopes = [.email, .fullName]
        
        let controller = ASAuthorizationController(authorizationRequests: [request])
        controller.delegate = self
        controller.presentationContextProvider = self
        controller.performRequests()
    }
    
    /// Sign in with email and password (for testing/development)
    func signIn(email: String, password: String) {
        isLoading = true
        errorMessage = nil
        
        let sessionRequest = MobileSessionRequest(
            email: email,
            password: password,
            deviceId: DeviceIdentifier.shared.deviceId ?? "",
            deviceType: "ios",
            appVersion: Bundle.main.appVersion,
            appleIdToken: nil
        )
        
        apiService.createMobileSession(request: sessionRequest)
            .receive(on: DispatchQueue.main)
            .sink(
                receiveCompletion: { [weak self] completion in
                    self?.isLoading = false
                    
                    switch completion {
                    case .finished:
                        break
                    case .failure(let error):
                        self?.errorMessage = error.localizedDescription
                    }
                },
                receiveValue: { [weak self] response in
                    self?.handleSuccessfulAuthentication(response)
                }
            )
            .store(in: &cancellables)
    }
    
    /// Sign out and clear stored credentials
    func signOut() {
        isLoading = true
        
        // Clear keychain
        _ = KeychainService.shared.clearAll()
        
        DispatchQueue.main.async {
            self.isAuthenticated = false
            self.currentUser = nil
            self.isLoading = false
            self.errorMessage = nil
        }
    }
    
    // MARK: - Private Methods
    
    /// Preload user data for performance optimization
    func preloadUserData() async {
        guard isAuthenticated else { return }
        
        // Preload subscription status
        do {
            let _ = try await apiService.getSubscriptionStatus().values.first(where: { _ in true })
        } catch {
            print("Failed to preload subscription status: \(error)")
        }
    }
    
    /// Handle successful authentication response
    private func handleSuccessfulAuthentication(_ response: MobileSessionResponse) {
        // Create user from session response
        let user = User(
            id: response.deviceInfo.deviceId, // Temporary ID
            email: response.userInfo.email,
            role: UserRole(rawValue: response.userInfo.role) ?? .free,
            subscriptionStatus: SubscriptionStatus(rawValue: response.userInfo.subscriptionStatus) ?? .none
        )
        
        self.currentUser = user
        self.isAuthenticated = true
        self.isLoading = false
        self.errorMessage = nil
    }
    
    /// Handle Sign in with Apple credential
    private func handleAppleIDCredential(_ credential: ASAuthorizationAppleIDCredential) {
        guard let identityTokenData = credential.identityToken,
              let identityToken = String(data: identityTokenData, encoding: .utf8) else {
            DispatchQueue.main.async {
                self.errorMessage = "Failed to get Apple ID token"
                self.isLoading = false
            }
            return
        }
        
        let email = credential.email ?? "unknown@apple.com"
        
        let sessionRequest = MobileSessionRequest(
            email: email,
            password: nil,
            deviceId: DeviceIdentifier.shared.deviceId ?? "",
            deviceType: "ios",
            appVersion: Bundle.main.appVersion,
            appleIdToken: identityToken
        )
        
        apiService.createMobileSession(request: sessionRequest)
            .receive(on: DispatchQueue.main)
            .sink(
                receiveCompletion: { [weak self] completion in
                    self?.isLoading = false
                    
                    switch completion {
                    case .finished:
                        break
                    case .failure(let error):
                        self?.errorMessage = error.localizedDescription
                    }
                },
                receiveValue: { [weak self] response in
                    self?.handleSuccessfulAuthentication(response)
                }
            )
            .store(in: &cancellables)
    }
}

// MARK: - ASAuthorizationControllerDelegate

extension AuthenticationService: ASAuthorizationControllerDelegate {
    
    func authorizationController(controller: ASAuthorizationController, didCompleteWithAuthorization authorization: ASAuthorization) {
        switch authorization.credential {
        case let appleIDCredential as ASAuthorizationAppleIDCredential:
            handleAppleIDCredential(appleIDCredential)
        default:
            DispatchQueue.main.async {
                self.errorMessage = "Unsupported authorization type"
                self.isLoading = false
            }
        }
    }
    
    func authorizationController(controller: ASAuthorizationController, didCompleteWithError error: Error) {
        DispatchQueue.main.async {
            self.errorMessage = error.localizedDescription
            self.isLoading = false
        }
    }
}

// MARK: - ASAuthorizationControllerPresentationContextProviding

extension AuthenticationService: ASAuthorizationControllerPresentationContextProviding {
    
    func presentationAnchor(for controller: ASAuthorizationController) -> ASPresentationAnchor {
        // Return the key window
        return UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .flatMap { $0.windows }
            .first { $0.isKeyWindow } ?? UIWindow()
    }
}