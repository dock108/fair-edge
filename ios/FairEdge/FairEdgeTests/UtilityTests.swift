//
//  UtilityTests.swift
//  FairEdgeTests
//
//  Unit tests for iOS utility functions and extensions
//  Tests device identification, formatting utilities, validation helpers, and string extensions

import XCTest
import UIKit
@testable import FairEdge

class UtilityTests: XCTestCase {
    
    // MARK: - DeviceIdentifier Tests
    
    func testDeviceIdentifier_Generation() throws {
        // When: Generating device identifier
        let deviceID1 = DeviceIdentifier.generate()
        let deviceID2 = DeviceIdentifier.generate()
        
        // Then: Should generate unique identifiers
        XCTAssertNotNil(deviceID1)
        XCTAssertNotNil(deviceID2)
        XCTAssertNotEqual(deviceID1, deviceID2)
        XCTAssertTrue(deviceID1.count > 10) // Reasonable length
    }
    
    func testDeviceIdentifier_Persistence() throws {
        // Given: Generated device identifier
        let originalID = DeviceIdentifier.generate()
        DeviceIdentifier.store(originalID)
        
        // When: Retrieving stored identifier
        let retrievedID = DeviceIdentifier.retrieve()
        
        // Then: Should retrieve same identifier
        XCTAssertEqual(retrievedID, originalID)
    }
    
    func testDeviceIdentifier_GetOrCreate() throws {
        // Given: No existing device identifier
        DeviceIdentifier.clear()
        
        // When: Getting or creating identifier
        let deviceID1 = DeviceIdentifier.getOrCreate()
        let deviceID2 = DeviceIdentifier.getOrCreate()
        
        // Then: Should return same identifier on subsequent calls
        XCTAssertEqual(deviceID1, deviceID2)
        XCTAssertNotNil(deviceID1)
    }
    
    func testDeviceIdentifier_Clear() throws {
        // Given: Stored device identifier
        let originalID = DeviceIdentifier.generate()
        DeviceIdentifier.store(originalID)
        XCTAssertNotNil(DeviceIdentifier.retrieve())
        
        // When: Clearing device identifier
        DeviceIdentifier.clear()
        
        // Then: Should remove stored identifier
        XCTAssertNil(DeviceIdentifier.retrieve())
    }
    
    // MARK: - Date Extension Tests
    
    func testDateFormatting_ISO8601() throws {
        // Given: Date
        let date = Date(timeIntervalSince1970: 1642780800) // January 21, 2022 12:00:00 UTC
        
        // When: Formatting to ISO8601
        let iso8601String = date.iso8601String
        
        // Then: Should format correctly
        XCTAssertEqual(iso8601String, "2022-01-21T12:00:00Z")
    }
    
    func testDateFormatting_Display() throws {
        // Given: Date
        let date = Date(timeIntervalSince1970: 1642780800) // January 21, 2022 12:00:00 UTC
        
        // When: Formatting for display
        let displayString = date.displayString
        
        // Then: Should format in readable format
        XCTAssertTrue(displayString.contains("Jan") || displayString.contains("January"))
        XCTAssertTrue(displayString.contains("21"))
        XCTAssertTrue(displayString.contains("2022"))
    }
    
    func testDateFormatting_TimeAgo() throws {
        // Given: Recent date
        let oneHourAgo = Date().addingTimeInterval(-3600)
        let oneDayAgo = Date().addingTimeInterval(-86400)
        let oneWeekAgo = Date().addingTimeInterval(-604800)
        
        // When: Getting time ago strings
        let hourAgoString = oneHourAgo.timeAgoString
        let dayAgoString = oneDayAgo.timeAgoString
        let weekAgoString = oneWeekAgo.timeAgoString
        
        // Then: Should format relative times
        XCTAssertTrue(hourAgoString.contains("hour") || hourAgoString.contains("1h"))
        XCTAssertTrue(dayAgoString.contains("day") || dayAgoString.contains("1d"))
        XCTAssertTrue(weekAgoString.contains("week") || weekAgoString.contains("1w"))
    }
    
    func testDateFormatting_GameTime() throws {
        // Given: Future game time
        let futureDate = Date().addingTimeInterval(7200) // 2 hours from now
        
        // When: Formatting game time
        let gameTimeString = futureDate.gameTimeString
        
        // Then: Should show time until game
        XCTAssertTrue(gameTimeString.contains("2") || gameTimeString.contains("hour"))
    }
    
    func testDateParsing_ISO8601() throws {
        // Given: ISO8601 string
        let iso8601String = "2022-01-21T12:00:00Z"
        
        // When: Parsing from string
        let parsedDate = Date.fromISO8601(iso8601String)
        
        // Then: Should parse correctly
        XCTAssertNotNil(parsedDate)
        XCTAssertEqual(parsedDate?.timeIntervalSince1970, 1642780800)
    }
    
    func testDateParsing_InvalidString() throws {
        // Given: Invalid date string
        let invalidString = "invalid-date"
        
        // When: Parsing invalid string
        let parsedDate = Date.fromISO8601(invalidString)
        
        // Then: Should return nil
        XCTAssertNil(parsedDate)
    }
    
    // MARK: - String Extension Tests
    
    func testStringValidation_Email() throws {
        // Given: Valid and invalid emails
        let validEmails = [
            "test@fair-edge.com",
            "user.name+tag@example.co.uk",
            "simple@example.org",
            "test123@gmail.com"
        ]
        
        let invalidEmails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user name@domain.com",
            "",
            "test@"
        ]
        
        // When: Validating emails
        for email in validEmails {
            // Then: Should be valid
            XCTAssertTrue(email.isValidEmail, "Email should be valid: \(email)")
        }
        
        for email in invalidEmails {
            // Then: Should be invalid
            XCTAssertFalse(email.isValidEmail, "Email should be invalid: \(email)")
        }
    }
    
    func testStringValidation_PhoneNumber() throws {
        // Given: Valid and invalid phone numbers
        let validPhones = [
            "+1234567890",
            "(555) 123-4567",
            "555-123-4567",
            "15551234567"
        ]
        
        let invalidPhones = [
            "123",
            "invalid-phone",
            "",
            "++1234567890"
        ]
        
        // When: Validating phone numbers
        for phone in validPhones {
            // Then: Should be valid
            XCTAssertTrue(phone.isValidPhoneNumber, "Phone should be valid: \(phone)")
        }
        
        for phone in invalidPhones {
            // Then: Should be invalid
            XCTAssertFalse(phone.isValidPhoneNumber, "Phone should be invalid: \(phone)")
        }
    }
    
    func testStringFormatting_PhoneNumber() throws {
        // Given: Raw phone number
        let rawPhone = "15551234567"
        
        // When: Formatting phone number
        let formattedPhone = rawPhone.formattedPhoneNumber
        
        // Then: Should format with standard format
        XCTAssertEqual(formattedPhone, "(555) 123-4567")
    }
    
    func testStringCleaning_RemoveWhitespace() throws {
        // Given: String with whitespace
        let stringWithWhitespace = "  test string  \n\t  "
        
        // When: Removing whitespace
        let cleanedString = stringWithWhitespace.trimmed
        
        // Then: Should remove leading/trailing whitespace
        XCTAssertEqual(cleanedString, "test string")
    }
    
    func testStringCleaning_RemoveSpecialCharacters() throws {
        // Given: String with special characters
        let stringWithSpecials = "test@#$%string!!"
        
        // When: Removing special characters
        let cleanedString = stringWithSpecials.alphanumericOnly
        
        // Then: Should keep only alphanumeric characters
        XCTAssertEqual(cleanedString, "teststring")
    }
    
    func testStringCapitalization() throws {
        // Given: Various strings
        let lowercase = "test string"
        let mixedCase = "tEsT StRiNg"
        
        // When: Capitalizing first letter
        let capitalizedFirst = lowercase.capitalizedFirst
        let titleCased = mixedCase.titleCased
        
        // Then: Should capitalize correctly
        XCTAssertEqual(capitalizedFirst, "Test string")
        XCTAssertEqual(titleCased, "Test String")
    }
    
    func testStringTruncation() throws {
        // Given: Long string
        let longString = "This is a very long string that needs to be truncated"
        
        // When: Truncating string
        let truncated = longString.truncated(to: 20)
        
        // Then: Should truncate with ellipsis
        XCTAssertEqual(truncated, "This is a very lo...")
        XCTAssertTrue(truncated.count <= 23) // 20 + "..."
    }
    
    func testStringTruncation_ShortString() throws {
        // Given: Short string
        let shortString = "Short"
        
        // When: Truncating string longer than its length
        let truncated = shortString.truncated(to: 20)
        
        // Then: Should return original string
        XCTAssertEqual(truncated, shortString)
    }
    
    // MARK: - Number Formatting Tests
    
    func testNumberFormatting_Currency() throws {
        // Given: Numeric values
        let price1 = 9.99
        let price2 = 1234.56
        let price3 = 0.99
        
        // When: Formatting as currency
        let formatted1 = price1.currencyString
        let formatted2 = price2.currencyString
        let formatted3 = price3.currencyString
        
        // Then: Should format with currency symbol
        XCTAssertEqual(formatted1, "$9.99")
        XCTAssertEqual(formatted2, "$1,234.56")
        XCTAssertEqual(formatted3, "$0.99")
    }
    
    func testNumberFormatting_Percentage() throws {
        // Given: Percentage values
        let percentage1 = 0.125
        let percentage2 = 0.8567
        let percentage3 = 1.25
        
        // When: Formatting as percentage
        let formatted1 = percentage1.percentageString
        let formatted2 = percentage2.percentageString(decimalPlaces: 2)
        let formatted3 = percentage3.percentageString
        
        // Then: Should format with percentage symbol
        XCTAssertEqual(formatted1, "12.5%")
        XCTAssertEqual(formatted2, "85.67%")
        XCTAssertEqual(formatted3, "125.0%")
    }
    
    func testNumberFormatting_Decimal() throws {
        // Given: Decimal values
        let decimal1 = 12.345678
        let decimal2 = 0.1
        let decimal3 = 1000.0
        
        // When: Formatting with specific decimal places
        let formatted1 = decimal1.decimalString(places: 2)
        let formatted2 = decimal2.decimalString(places: 3)
        let formatted3 = decimal3.decimalString(places: 0)
        
        // Then: Should format with correct decimal places
        XCTAssertEqual(formatted1, "12.35")
        XCTAssertEqual(formatted2, "0.100")
        XCTAssertEqual(formatted3, "1000")
    }
    
    // MARK: - Odds Conversion Tests
    
    func testOddsConversion_AmericanToDecimal() throws {
        // Given: American odds
        let positiveOdds = "+150"
        let negativeOdds = "-110"
        let evenOdds = "+100"
        
        // When: Converting to decimal
        let decimal1 = positiveOdds.toDecimalOdds()
        let decimal2 = negativeOdds.toDecimalOdds()
        let decimal3 = evenOdds.toDecimalOdds()
        
        // Then: Should convert correctly
        XCTAssertEqual(decimal1, 2.5, accuracy: 0.01)
        XCTAssertEqual(decimal2, 1.909, accuracy: 0.01)
        XCTAssertEqual(decimal3, 2.0, accuracy: 0.01)
    }
    
    func testOddsConversion_DecimalToAmerican() throws {
        // Given: Decimal odds
        let decimal1 = 2.5
        let decimal2 = 1.909
        let decimal3 = 2.0
        
        // When: Converting to American
        let american1 = decimal1.toAmericanOdds()
        let american2 = decimal2.toAmericanOdds()
        let american3 = decimal3.toAmericanOdds()
        
        // Then: Should convert correctly
        XCTAssertEqual(american1, "+150")
        XCTAssertEqual(american2, "-110")
        XCTAssertEqual(american3, "+100")
    }
    
    func testOddsConversion_InvalidFormat() throws {
        // Given: Invalid odds format
        let invalidOdds = "invalid"
        
        // When: Converting invalid odds
        let decimal = invalidOdds.toDecimalOdds()
        
        // Then: Should return nil or default
        XCTAssertNil(decimal)
    }
    
    func testOddsValidation() throws {
        // Given: Valid and invalid odds
        let validOdds = ["+150", "-110", "+100", "-200", "+250"]
        let invalidOdds = ["invalid", "150", "-", "+", "0"]
        
        // When: Validating odds
        for odds in validOdds {
            // Then: Should be valid
            XCTAssertTrue(odds.isValidAmericanOdds, "Odds should be valid: \(odds)")
        }
        
        for odds in invalidOdds {
            // Then: Should be invalid
            XCTAssertFalse(odds.isValidAmericanOdds, "Odds should be invalid: \(odds)")
        }
    }
    
    // MARK: - Color Extension Tests
    
    func testColorFromHex() throws {
        // Given: Hex color codes
        let redHex = "#FF0000"
        let greenHex = "#00FF00"
        let blueHex = "#0000FF"
        let shortHex = "#FFF"
        
        // When: Creating colors from hex
        let redColor = UIColor.from(hex: redHex)
        let greenColor = UIColor.from(hex: greenHex)
        let blueColor = UIColor.from(hex: blueHex)
        let whiteColor = UIColor.from(hex: shortHex)
        
        // Then: Should create correct colors
        XCTAssertNotNil(redColor)
        XCTAssertNotNil(greenColor)
        XCTAssertNotNil(blueColor)
        XCTAssertNotNil(whiteColor)
    }
    
    func testColorFromInvalidHex() throws {
        // Given: Invalid hex codes
        let invalidHex = "invalid"
        
        // When: Creating color from invalid hex
        let color = UIColor.from(hex: invalidHex)
        
        // Then: Should return nil or default
        XCTAssertNil(color)
    }
    
    func testColorToHex() throws {
        // Given: Standard colors
        let redColor = UIColor.red
        let greenColor = UIColor.green
        let blueColor = UIColor.blue
        
        // When: Converting to hex
        let redHex = redColor.hexString
        let greenHex = greenColor.hexString
        let blueHex = blueColor.hexString
        
        // Then: Should convert to hex strings
        XCTAssertEqual(redHex.uppercased(), "#FF0000")
        XCTAssertEqual(greenHex.uppercased(), "#00FF00")
        XCTAssertEqual(blueHex.uppercased(), "#0000FF")
    }
    
    // MARK: - Array Extension Tests
    
    func testArraySafeAccess() throws {
        // Given: Array with elements
        let array = ["first", "second", "third"]
        
        // When: Safely accessing elements
        let validElement = array.safe(at: 1)
        let invalidElement = array.safe(at: 10)
        
        // Then: Should return element or nil
        XCTAssertEqual(validElement, "second")
        XCTAssertNil(invalidElement)
    }
    
    func testArrayChunking() throws {
        // Given: Array of numbers
        let numbers = Array(1...10)
        
        // When: Chunking array
        let chunks = numbers.chunked(into: 3)
        
        // Then: Should create correct chunks
        XCTAssertEqual(chunks.count, 4) // [1,2,3], [4,5,6], [7,8,9], [10]
        XCTAssertEqual(chunks[0], [1, 2, 3])
        XCTAssertEqual(chunks[1], [4, 5, 6])
        XCTAssertEqual(chunks[2], [7, 8, 9])
        XCTAssertEqual(chunks[3], [10])
    }
    
    func testArrayUnique() throws {
        // Given: Array with duplicates
        let arrayWithDuplicates = [1, 2, 2, 3, 3, 3, 4]
        
        // When: Getting unique elements
        let uniqueArray = arrayWithDuplicates.unique()
        
        // Then: Should remove duplicates
        XCTAssertEqual(uniqueArray.sorted(), [1, 2, 3, 4])
    }
    
    // MARK: - Dictionary Extension Tests
    
    func testDictionaryMerge() throws {
        // Given: Two dictionaries
        let dict1 = ["a": 1, "b": 2]
        let dict2 = ["b": 3, "c": 4]
        
        // When: Merging dictionaries
        let merged = dict1.merging(dict2)
        
        // Then: Should merge with dict2 values taking precedence
        XCTAssertEqual(merged["a"], 1)
        XCTAssertEqual(merged["b"], 3) // dict2 value
        XCTAssertEqual(merged["c"], 4)
    }
    
    func testDictionaryMapValues() throws {
        // Given: Dictionary with integer values
        let numbers = ["one": 1, "two": 2, "three": 3]
        
        // When: Mapping values
        let doubled = numbers.mapValues { $0 * 2 }
        
        // Then: Should transform values
        XCTAssertEqual(doubled["one"], 2)
        XCTAssertEqual(doubled["two"], 4)
        XCTAssertEqual(doubled["three"], 6)
    }
    
    // MARK: - UserDefaults Extension Tests
    
    func testUserDefaultsObjectStorage() throws {
        // Given: Custom object
        let preferences = createMockPreferences()
        let key = "test_preferences"
        
        // When: Storing and retrieving object
        UserDefaults.standard.setObject(preferences, for: key)
        let retrieved: MockPreferences? = UserDefaults.standard.getObject(for: key)
        
        // Then: Should store and retrieve correctly
        XCTAssertNotNil(retrieved)
        XCTAssertEqual(retrieved?.theme, preferences.theme)
        XCTAssertEqual(retrieved?.notificationsEnabled, preferences.notificationsEnabled)
        
        // Cleanup
        UserDefaults.standard.removeObject(forKey: key)
    }
    
    // MARK: - Validation Utilities Tests
    
    func testStrongPasswordValidation() throws {
        // Given: Various passwords
        let strongPasswords = [
            "StrongPass123!",
            "MyP@ssw0rd",
            "Secure123$"
        ]
        
        let weakPasswords = [
            "weak",
            "password",
            "12345678",
            "PASSWORD"
        ]
        
        // When: Validating passwords
        for password in strongPasswords {
            // Then: Should be strong
            XCTAssertTrue(ValidationUtils.isStrongPassword(password), "Password should be strong: \(password)")
        }
        
        for password in weakPasswords {
            // Then: Should be weak
            XCTAssertFalse(ValidationUtils.isStrongPassword(password), "Password should be weak: \(password)")
        }
    }
    
    func testCreditCardValidation() throws {
        // Given: Valid and invalid credit card numbers
        let validCards = [
            "4111111111111111", // Visa
            "5555555555554444", // MasterCard
            "378282246310005"   // American Express
        ]
        
        let invalidCards = [
            "1234567890123456",
            "invalid",
            "",
            "4111111111111112" // Invalid checksum
        ]
        
        // When: Validating credit cards
        for card in validCards {
            // Then: Should be valid
            XCTAssertTrue(ValidationUtils.isValidCreditCard(card), "Card should be valid: \(card)")
        }
        
        for card in invalidCards {
            // Then: Should be invalid
            XCTAssertFalse(ValidationUtils.isValidCreditCard(card), "Card should be invalid: \(card)")
        }
    }
    
    // MARK: - Performance Tests
    
    func testDeviceIdentifierPerformance() throws {
        // When: Generating multiple device identifiers
        measure {
            for _ in 0..<1000 {
                _ = DeviceIdentifier.generate()
            }
        }
    }
    
    func testStringValidationPerformance() throws {
        // Given: Large number of strings to validate
        let emails = Array(0..<1000).map { "test\($0)@example.com" }
        
        // When: Validating all emails
        measure {
            for email in emails {
                _ = email.isValidEmail
            }
        }
    }
    
    func testOddsConversionPerformance() throws {
        // Given: Large number of odds to convert
        let odds = Array(0..<1000).map { "+\(100 + $0)" }
        
        // When: Converting all odds
        measure {
            for odd in odds {
                _ = odd.toDecimalOdds()
            }
        }
    }
}

// MARK: - Test Utilities

extension UtilityTests {
    
    func createMockPreferences() -> MockPreferences {
        return MockPreferences(
            theme: "dark",
            notificationsEnabled: true,
            evThreshold: 5.0
        )
    }
}

// MARK: - Mock Objects

struct MockPreferences: Codable {
    let theme: String
    let notificationsEnabled: Bool
    let evThreshold: Double
}

// MARK: - Utility Classes

class DeviceIdentifier {
    private static let keychain = KeychainService(serviceName: "com.fairedge.device")
    private static let deviceIDKey = "device_identifier"
    
    static func generate() -> String {
        return UUID().uuidString
    }
    
    static func store(_ identifier: String) {
        keychain.save(identifier, for: deviceIDKey)
    }
    
    static func retrieve() -> String? {
        return keychain.get(for: deviceIDKey)
    }
    
    static func getOrCreate() -> String {
        if let existing = retrieve() {
            return existing
        }
        let new = generate()
        store(new)
        return new
    }
    
    static func clear() {
        keychain.delete(for: deviceIDKey)
    }
}

class ValidationUtils {
    
    static func isStrongPassword(_ password: String) -> Bool {
        // At least 8 characters, contains uppercase, lowercase, number, and special character
        let length = password.count >= 8
        let hasUpper = password.range(of: "[A-Z]", options: .regularExpression) != nil
        let hasLower = password.range(of: "[a-z]", options: .regularExpression) != nil
        let hasNumber = password.range(of: "[0-9]", options: .regularExpression) != nil
        let hasSpecial = password.range(of: "[^A-Za-z0-9]", options: .regularExpression) != nil
        
        return length && hasUpper && hasLower && hasNumber && hasSpecial
    }
    
    static func isValidCreditCard(_ number: String) -> Bool {
        let cleaned = number.replacingOccurrences(of: " ", with: "")
        guard cleaned.allSatisfy({ $0.isNumber }) else { return false }
        guard cleaned.count >= 13 && cleaned.count <= 19 else { return false }
        
        // Luhn algorithm
        let digits = cleaned.compactMap { Int(String($0)) }
        var sum = 0
        var isSecond = false
        
        for i in stride(from: digits.count - 1, through: 0, by: -1) {
            var digit = digits[i]
            
            if isSecond {
                digit *= 2
                if digit > 9 {
                    digit = digit % 10 + digit / 10
                }
            }
            
            sum += digit
            isSecond.toggle()
        }
        
        return sum % 10 == 0
    }
}

// MARK: - Extensions

extension Date {
    var iso8601String: String {
        let formatter = ISO8601DateFormatter()
        return formatter.string(from: self)
    }
    
    var displayString: String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: self)
    }
    
    var timeAgoString: String {
        let interval = Date().timeIntervalSince(self)
        
        if interval < 60 {
            return "Just now"
        } else if interval < 3600 {
            let minutes = Int(interval / 60)
            return "\(minutes)m ago"
        } else if interval < 86400 {
            let hours = Int(interval / 3600)
            return "\(hours)h ago"
        } else {
            let days = Int(interval / 86400)
            return "\(days)d ago"
        }
    }
    
    var gameTimeString: String {
        let interval = self.timeIntervalSince(Date())
        
        if interval < 0 {
            return "Game started"
        } else if interval < 3600 {
            let minutes = Int(interval / 60)
            return "\(minutes)m"
        } else if interval < 86400 {
            let hours = Int(interval / 3600)
            return "\(hours)h"
        } else {
            let days = Int(interval / 86400)
            return "\(days)d"
        }
    }
    
    static func fromISO8601(_ string: String) -> Date? {
        let formatter = ISO8601DateFormatter()
        return formatter.date(from: string)
    }
}

extension String {
    var isValidEmail: Bool {
        let emailRegex = "^[A-Z0-9a-z._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$"
        return NSPredicate(format: "SELF MATCHES %@", emailRegex).evaluate(with: self)
    }
    
    var isValidPhoneNumber: Bool {
        let phoneRegex = "^[\\+]?[1-9]?[0-9]{7,14}$"
        let cleaned = self.replacingOccurrences(of: "[^0-9+]", with: "", options: .regularExpression)
        return NSPredicate(format: "SELF MATCHES %@", phoneRegex).evaluate(with: cleaned)
    }
    
    var formattedPhoneNumber: String {
        let cleaned = self.replacingOccurrences(of: "[^0-9]", with: "", options: .regularExpression)
        guard cleaned.count == 11, cleaned.hasPrefix("1") else { return self }
        
        let areaCode = String(cleaned.dropFirst().prefix(3))
        let firstThree = String(cleaned.dropFirst(4).prefix(3))
        let lastFour = String(cleaned.dropFirst(7))
        
        return "(\(areaCode)) \(firstThree)-\(lastFour)"
    }
    
    var trimmed: String {
        return self.trimmingCharacters(in: .whitespacesAndNewlines)
    }
    
    var alphanumericOnly: String {
        return self.replacingOccurrences(of: "[^A-Za-z0-9]", with: "", options: .regularExpression)
    }
    
    var capitalizedFirst: String {
        guard !isEmpty else { return self }
        return prefix(1).uppercased() + dropFirst().lowercased()
    }
    
    var titleCased: String {
        return self.capitalized
    }
    
    func truncated(to length: Int) -> String {
        guard self.count > length else { return self }
        return String(self.prefix(length)) + "..."
    }
    
    func toDecimalOdds() -> Double? {
        let cleaned = self.trimmingCharacters(in: .whitespaces)
        
        if cleaned.hasPrefix("+") {
            guard let value = Double(String(cleaned.dropFirst())) else { return nil }
            return (value / 100) + 1
        } else if cleaned.hasPrefix("-") {
            guard let value = Double(String(cleaned.dropFirst())) else { return nil }
            return (100 / value) + 1
        }
        
        return nil
    }
    
    var isValidAmericanOdds: Bool {
        let oddsRegex = "^[+-][0-9]+$"
        return NSPredicate(format: "SELF MATCHES %@", oddsRegex).evaluate(with: self)
    }
}

extension Double {
    var currencyString: String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.locale = Locale(identifier: "en_US")
        return formatter.string(from: NSNumber(value: self)) ?? "$0.00"
    }
    
    func percentageString(decimalPlaces: Int = 1) -> String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .percent
        formatter.minimumFractionDigits = decimalPlaces
        formatter.maximumFractionDigits = decimalPlaces
        return formatter.string(from: NSNumber(value: self)) ?? "0%"
    }
    
    func decimalString(places: Int) -> String {
        return String(format: "%.\(places)f", self)
    }
    
    func toAmericanOdds() -> String {
        if self >= 2.0 {
            let value = Int((self - 1) * 100)
            return "+\(value)"
        } else {
            let value = Int(100 / (self - 1))
            return "-\(value)"
        }
    }
}

extension UIColor {
    static func from(hex: String) -> UIColor? {
        var hexString = hex.trimmingCharacters(in: .whitespacesAndNewlines)
        hexString = hexString.replacingOccurrences(of: "#", with: "")
        
        var rgb: UInt64 = 0
        guard Scanner(string: hexString).scanHexInt64(&rgb) else { return nil }
        
        if hexString.count == 3 {
            let r = Double((rgb & 0xF00) >> 8) / 15.0
            let g = Double((rgb & 0x0F0) >> 4) / 15.0
            let b = Double(rgb & 0x00F) / 15.0
            return UIColor(red: r, green: g, blue: b, alpha: 1.0)
        } else if hexString.count == 6 {
            let r = Double((rgb & 0xFF0000) >> 16) / 255.0
            let g = Double((rgb & 0x00FF00) >> 8) / 255.0
            let b = Double(rgb & 0x0000FF) / 255.0
            return UIColor(red: r, green: g, blue: b, alpha: 1.0)
        }
        
        return nil
    }
    
    var hexString: String {
        var r: CGFloat = 0
        var g: CGFloat = 0
        var b: CGFloat = 0
        var a: CGFloat = 0
        
        getRed(&r, green: &g, blue: &b, alpha: &a)
        
        let rgb = Int(r * 255) << 16 | Int(g * 255) << 8 | Int(b * 255)
        return String(format: "#%06x", rgb)
    }
}

extension Array {
    func safe(at index: Int) -> Element? {
        return indices.contains(index) ? self[index] : nil
    }
    
    func chunked(into size: Int) -> [[Element]] {
        return stride(from: 0, to: count, by: size).map {
            Array(self[$0..<Swift.min($0 + size, count)])
        }
    }
}

extension Array where Element: Hashable {
    func unique() -> [Element] {
        return Array(Set(self))
    }
}

extension Dictionary {
    func merging(_ other: [Key: Value]) -> [Key: Value] {
        return self.merging(other) { _, new in new }
    }
}

extension UserDefaults {
    func setObject<T: Codable>(_ object: T, for key: String) {
        let encoder = JSONEncoder()
        if let data = try? encoder.encode(object) {
            set(data, forKey: key)
        }
    }
    
    func getObject<T: Codable>(for key: String, type: T.Type = T.self) -> T? {
        guard let data = data(forKey: key) else { return nil }
        let decoder = JSONDecoder()
        return try? decoder.decode(type, from: data)
    }
}