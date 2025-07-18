//
//  ContentView.swift
//  FairEdge
//
//  Created by Fair-Edge on 1/18/25.
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var authenticationService: AuthenticationService
    
    var body: some View {
        NavigationView {
            if authenticationService.isAuthenticated {
                OpportunitiesListView()
            } else {
                AuthenticationView()
            }
        }
        .onAppear {
            authenticationService.checkAuthenticationStatus()
        }
    }
}