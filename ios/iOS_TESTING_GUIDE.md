# Fair-Edge iOS Testing Guide

## 🎯 **Overview**

This guide covers the comprehensive iOS testing infrastructure for the Fair-Edge betting platform. Our iOS testing framework achieves 75%+ code coverage and follows Apple's best practices for unit testing, UI testing, and performance testing.

## 📊 **Testing Architecture**

### **Test Structure**
```
FairEdgeTests/
├── Service Tests
│   ├── PushNotificationServiceTests.swift    # APNs integration testing
│   ├── WebSocketServiceTests.swift           # Real-time connection testing
│   ├── AnalyticsServiceTests.swift           # Event tracking & crash reporting
│   ├── KeychainServiceTests.swift            # Secure storage testing
│   ├── APIServiceTests.swift                 # Backend integration testing
│   ├── AuthenticationServiceTests.swift      # Authentication flow testing
│   └── StoreKitServiceTests.swift            # In-app purchase testing
├── Model Tests
│   └── ModelTests.swift                      # Data model validation
├── Utility Tests
│   └── UtilityTests.swift                    # Helper functions & extensions
├── ViewModel Tests
│   └── ViewModelTests.swift                  # Business logic & state management
└── Test Utilities
    └── FairEdgeTests.swift                   # Shared test fixtures

FairEdgeUITests/
└── FairEdgeUITests.swift                     # End-to-end user flow testing
```

## 🧪 **Test Categories**

### **1. Service Layer Tests (7 files, 200+ tests)**

#### **PushNotificationServiceTests.swift**
- **APNs Integration**: Device token registration, notification handling
- **Permission Management**: User consent, settings synchronization
- **Background Processing**: Silent notifications, content updates
- **Error Handling**: Permission denial, network failures

```swift
func testRegisterDeviceToken_Success() throws {
    // Given: Valid device token
    let deviceToken = Data([0x01, 0x02, 0x03, 0x04, 0x05])
    mockAPIService.shouldRegisterDeviceSucceed = true

    // When: Registering device token
    pushService.didRegisterForRemoteNotifications(withDeviceToken: deviceToken)

    // Then: Should register with API successfully
    XCTAssertEqual(pushService.deviceToken, deviceToken.hexString)
}
```

#### **WebSocketServiceTests.swift**
- **Real-time Connections**: Connection management, auto-reconnection
- **Message Handling**: Opportunity updates, user notifications
- **Authentication Integration**: Token refresh, session management
- **Network Resilience**: Connection loss, retry logic

#### **AnalyticsServiceTests.swift**
- **Event Tracking**: User interactions, business metrics
- **Privacy Compliance**: Data scrubbing, opt-out functionality
- **Crash Reporting**: Error collection, reporting workflows
- **Performance Monitoring**: Session tracking, device metrics

#### **KeychainServiceTests.swift**
- **Secure Storage**: Token persistence, credential management
- **Migration Support**: Legacy data handling, service updates
- **Concurrent Access**: Thread safety, data integrity
- **Security Validation**: Access controls, data encryption

### **2. Model Layer Tests (1 file, 60+ tests)**

#### **ModelTests.swift**
- **Data Validation**: Input sanitization, format checking
- **Business Logic**: EV calculations, user permissions
- **Serialization**: JSON encoding/decoding, data consistency
- **Edge Cases**: Boundary conditions, error scenarios

```swift
func testBettingOpportunityModel_Classifications() throws {
    // Given: Opportunity with high EV
    let opportunity = BettingOpportunity(evPercentage: 15.0, ...)

    // When: Checking classification
    // Then: Should be classified as high value
    XCTAssertTrue(opportunity.isHighValue)
    XCTAssertTrue(opportunity.shouldNotify)
}
```

### **3. Utility Layer Tests (1 file, 50+ tests)**

#### **UtilityTests.swift**
- **Device Identification**: UUID generation, persistence
- **Data Formatting**: Currency, percentages, dates
- **Validation Helpers**: Email, phone number, password strength
- **Extensions**: String manipulation, color conversion

### **4. ViewModel Tests (1 file, 25+ tests)**

#### **ViewModelTests.swift**
- **State Management**: ObservableObject updates, data binding
- **Business Logic**: Filtering, sorting, search functionality
- **Error Handling**: Network failures, validation errors
- **User Interactions**: Authentication, subscription management

### **5. UI Tests (1 file, 40+ tests)**

#### **FairEdgeUITests.swift**
- **Complete User Flows**: Authentication to subscription
- **Navigation Testing**: Tab bar, modal presentations
- **Accessibility**: VoiceOver, dynamic type support
- **Performance**: Launch time, scrolling responsiveness

## 🛠 **Running Tests**

### **Command Line Testing**

```bash
# Run all unit tests
cd ios/FairEdge
xcodebuild test -scheme FairEdge -destination "platform=iOS Simulator,name=iPhone 15,OS=17.0"

# Run tests with coverage
xcodebuild test -scheme FairEdge \
  -destination "platform=iOS Simulator,name=iPhone 15,OS=17.0" \
  -enableCodeCoverage YES

# Run specific test class
xcodebuild test -scheme FairEdge \
  -destination "platform=iOS Simulator,name=iPhone 15,OS=17.0" \
  -only-testing:FairEdgeTests/PushNotificationServiceTests

# Run UI tests only
xcodebuild test -scheme FairEdge \
  -destination "platform=iOS Simulator,name=iPhone 15,OS=17.0" \
  -testPlan FairEdgeUITests
```

### **Xcode IDE Testing**

1. **Unit Tests**: ⌘+U to run all tests
2. **Individual Tests**: Click the diamond icon next to test methods
3. **Test Coverage**: Enable in scheme settings → Test → Code Coverage
4. **UI Tests**: Select FairEdgeUITests scheme and run

### **CI/CD Integration**

Tests run automatically on:
- Pull requests to main/develop branches
- Pushes to main/develop branches
- Manual workflow dispatch

Coverage reports are uploaded to Codecov for tracking.

## 🎯 **Test Coverage Goals**

### **Current Coverage: 75%+**
- **Services**: 85%+ coverage (critical business logic)
- **Models**: 90%+ coverage (data validation)
- **ViewModels**: 80%+ coverage (UI logic)
- **Utilities**: 70%+ coverage (helper functions)

### **Coverage Requirements**
- **Minimum**: 75% overall coverage
- **Critical Paths**: 90%+ coverage (authentication, payments)
- **New Code**: 80%+ coverage required for PR approval

## 📝 **Writing New Tests**

### **Test Structure Pattern**

```swift
class NewServiceTests: XCTestCase {

    // MARK: - Properties
    var serviceUnderTest: NewService!
    var mockDependency: MockDependency!
    var cancellables: Set<AnyCancellable>!

    // MARK: - Setup & Teardown
    override func setUpWithError() throws {
        try super.setUpWithError()
        mockDependency = MockDependency()
        serviceUnderTest = NewService(dependency: mockDependency)
        cancellables = Set<AnyCancellable>()
    }

    override func tearDownWithError() throws {
        serviceUnderTest = nil
        mockDependency = nil
        cancellables.removeAll()
        try super.tearDownWithError()
    }

    // MARK: - Tests
    func testMethodName_Condition_ExpectedResult() throws {
        // Given: Setup test conditions

        // When: Execute the action being tested

        // Then: Assert expected outcomes
    }
}
```

### **Mock Object Pattern**

```swift
class MockAPIService {
    var shouldSucceed = true
    var mockResponse: APIResponse?
    var methodCallCount = 0

    func performRequest() async throws -> APIResponse {
        methodCallCount += 1

        if shouldSucceed {
            return mockResponse ?? APIResponse.default
        } else {
            throw APIError.networkFailure
        }
    }
}
```

### **Async Testing Pattern**

```swift
func testAsyncOperation() async throws {
    // Given: Async operation setup
    let expectation = XCTestExpectation(description: "Async operation completes")

    // When: Performing async operation
    let result = await serviceUnderTest.performAsyncOperation()

    // Then: Verify results
    XCTAssertNotNil(result)
    expectation.fulfill()

    await fulfillment(of: [expectation], timeout: 5.0)
}
```

## 🔧 **Test Utilities & Helpers**

### **Shared Test Fixtures**

```swift
extension XCTestCase {
    func createMockOpportunity() -> BettingOpportunity {
        return BettingOpportunity(
            id: "test_123",
            event: "Test Game",
            evPercentage: 10.0,
            // ... other properties
        )
    }

    func createMockUser() -> User {
        return User(
            id: "user_123",
            email: "test@example.com",
            role: .premium
        )
    }
}
```

### **Mock Service Factory**

```swift
class MockServiceFactory {
    static func createMockAPIService() -> MockAPIService {
        let service = MockAPIService()
        service.shouldSucceed = true
        return service
    }

    static func createMockAuthService() -> MockAuthenticationService {
        let service = MockAuthenticationService()
        service.isAuthenticated = true
        return service
    }
}
```

## 🚀 **Performance Testing**

### **Performance Test Pattern**

```swift
func testPerformanceOfCriticalOperation() throws {
    // Given: Large dataset
    let opportunities = createLargeOpportunityDataset()

    // When: Measuring performance
    measure {
        viewModel.filterOpportunities(opportunities)
    }

    // Baseline: < 0.1 seconds for 1000 items
}
```

### **Memory Testing**

```swift
func testMemoryUsage() throws {
    measure(metrics: [XCTMemoryMetric()]) {
        // Perform memory-intensive operations
        let largeDataSet = createLargeDataSet()
        viewModel.processData(largeDataSet)
    }
}
```

## 🛡️ **Security Testing**

### **Data Protection Tests**

```swift
func testSensitiveDataHandling() throws {
    // Given: Sensitive user data
    let sensitiveData = "user_password_123"

    // When: Storing data
    keychainService.store(sensitiveData, for: "password")

    // Then: Should not be accessible without authentication
    XCTAssertNil(keychainService.getWithoutAuth(for: "password"))
}
```

### **Network Security Tests**

```swift
func testAPICallSecurity() throws {
    // Given: API request
    let request = APIRequest(endpoint: "/secure-data")

    // When: Making request
    apiService.perform(request)

    // Then: Should include security headers
    XCTAssertTrue(request.headers.contains("Authorization"))
    XCTAssertTrue(request.url.scheme == "https")
}
```

## 🔍 **Debugging Tests**

### **Test Debugging Tips**

1. **Breakpoints**: Set breakpoints in test methods for step-by-step debugging
2. **Console Logging**: Use `print()` statements to trace execution
3. **Test Execution Order**: Tests run in alphabetical order by default
4. **Simulator State**: Reset simulator between test runs for consistency

### **Common Test Failures**

1. **Timing Issues**: Use `XCTestExpectation` for async operations
2. **State Pollution**: Ensure proper cleanup in `tearDown`
3. **Mock Configuration**: Verify mock objects are properly configured
4. **Threading Issues**: Use `@MainActor` for UI-related tests

## 📊 **Coverage Analysis**

### **Viewing Coverage Reports**

1. **Xcode**: Product → Test → Code Coverage (after running tests)
2. **Command Line**: Use `xcov` gem for detailed reports
3. **CI/CD**: Coverage reports uploaded to Codecov automatically

### **Coverage Exclusions**

Certain code is excluded from coverage requirements:
- Generated code (Core Data models)
- Third-party integrations
- Debug-only code
- UI preview code

## 🎉 **Best Practices**

### **DO:**
- ✅ Write descriptive test names: `testMethod_Condition_ExpectedResult`
- ✅ Use Given-When-Then structure for clarity
- ✅ Test edge cases and error conditions
- ✅ Mock external dependencies
- ✅ Keep tests focused and atomic
- ✅ Run tests frequently during development

### **DON'T:**
- ❌ Test internal implementation details
- ❌ Create tests that depend on network connectivity
- ❌ Write overly complex test setups
- ❌ Skip error case testing
- ❌ Use hardcoded timing in async tests
- ❌ Leave failing tests in the codebase

## 📈 **Continuous Improvement**

### **Test Quality Metrics**
- **Test Coverage**: Tracked via Codecov
- **Test Performance**: CI execution time monitoring
- **Test Reliability**: Flaky test detection and resolution
- **Code Quality**: SwiftLint integration for test code

### **Regular Reviews**
- Monthly test coverage review
- Quarterly test performance analysis
- Annual testing strategy assessment
- Continuous feedback from development team

---

## 🆘 **Troubleshooting**

### **Common Issues**

**Tests fail in CI but pass locally:**
- Check simulator versions match
- Verify environment variables are set
- Review timing-sensitive operations

**Coverage reports inaccurate:**
- Ensure code coverage is enabled in scheme
- Check for excluded files in configuration
- Verify test execution includes all targets

**UI tests are flaky:**
- Add proper wait conditions
- Use accessibility identifiers
- Check for animation timing issues

**Performance tests inconsistent:**
- Run on consistent hardware
- Minimize background processes
- Use relative performance baselines

### **Getting Help**

1. **Documentation**: Check this guide first
2. **Team Chat**: Ask in #ios-development channel
3. **Code Review**: Request testing feedback in PRs
4. **Apple Documentation**: Refer to XCTest framework docs

---

**Last Updated**: December 2024
**Version**: 1.0
**Maintainers**: iOS Development Team
