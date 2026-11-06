/// <reference types="cypress" />

describe('Twitch Clipper GUI', () => {
  beforeEach(() => {
    // Start the app (in real test, this would launch the Electron app)
    cy.visit('http://localhost:5173')
  })

  it('should load the dashboard', () => {
    cy.contains('h2', 'Dashboard').should('be.visible')
    cy.contains('Total de Clips').should('be.visible')
    cy.contains('Clips Prontos').should('be.visible')
  })

  it('should navigate to Clips page', () => {
    cy.contains('a', 'Clips').click()
    cy.contains('h2', 'Clips').should('be.visible')
    cy.contains('Buscar clips...').should('be.visible')
  })

  it('should navigate to Jobs page', () => {
    cy.contains('a', 'Jobs').click()
    cy.contains('h2', 'Jobs').should('be.visible')
  })

  it('should navigate to Live page', () => {
    cy.contains('a', 'Ao Vivo').click()
    cy.contains('h2', 'Monitoramento Ao Vivo').should('be.visible')
  })

  it('should navigate to Settings page', () => {
    cy.contains('a', 'Configurações').click()
    cy.contains('h2', 'Configurações').should('be.visible')
  })

  it('should show setup wizard on first run', () => {
    // This would require clearing localStorage/session
    // cy.clearLocalStorage()
    // cy.reload()
    // cy.contains('Bem-vindo ao Twitch Clipper!').should('be.visible')
  })

  it('should have working video player on Clips page', () => {
    cy.contains('a', 'Clips').click()
    // Video player test would require actual clips
  })
})