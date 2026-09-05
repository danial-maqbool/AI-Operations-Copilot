import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { MorningReviewModal } from './components/MorningReviewModal';
import { CommandPalette } from './components/CommandPalette';
import { Customer360Modal } from './components/Customer360Modal';

import { DashboardView } from './views/DashboardView';
import { CopilotView } from './views/CopilotView';
import { DataSourcesView } from './views/DataSourcesView';
import { CatalogView } from './views/CatalogView';
import { MetricsView } from './views/MetricsView';
import { ExceptionsView } from './views/ExceptionsView';
import { ActionCenterView } from './views/ActionCenterView';
import { WorkflowView } from './views/WorkflowView';
import { KnowledgeBaseView } from './views/KnowledgeBaseView';
import { ReportsView } from './views/ReportsView';
import { AuditView } from './views/AuditView';

import { api } from './services/api';
import { MorningReviewData } from './types';

export function App() {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [openExceptionsCount, setOpenExceptionsCount] = useState<number>(0);
  const [proposedActionsCount, setProposedActionsCount] = useState<number>(0);

  // Modals & Drawers
  const [morningReviewData, setMorningReviewData] = useState<MorningReviewData | null>(null);
  const [isMorningReviewOpen, setIsMorningReviewOpen] = useState<boolean>(false);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState<boolean>(false);
  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(null);

  const [isLoadingDemo, setIsLoadingDemo] = useState<boolean>(false);
  const [isRunningReview, setIsRunningReview] = useState<boolean>(false);

  useEffect(() => {
    loadCounts();
  }, [activeTab]);

  const loadCounts = async () => {
    try {
      const [excs, acts] = await Promise.all([
        api.getExceptions(),
        api.getActions('PROPOSED')
      ]);
      setOpenExceptionsCount(excs.filter((e: any) => e.status === 'OPEN').length);
      setProposedActionsCount(acts.length);
    } catch (err) {
      // Quietly continue if backend is starting
    }
  };

  const handleRunMorningReview = async () => {
    setIsRunningReview(true);
    try {
      const review = await api.runMorningReview();
      setMorningReviewData(review);
      setIsMorningReviewOpen(true);
      loadCounts();
    } catch (err) {
      alert('Failed to execute morning review: ' + err);
    } finally {
      setIsRunningReview(false);
    }
  };

  const handleLoadDemo = async () => {
    setIsLoadingDemo(true);
    try {
      await api.loadDemoCompany();
      alert('Demo company dataset successfully loaded with 10 tables, 4 policy documents, and seeded exceptions!');
      loadCounts();
      window.location.reload();
    } catch (err) {
      alert('Failed to load demo dataset: ' + err);
    } finally {
      setIsLoadingDemo(false);
    }
  };

  const renderActiveView = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardView onNavigate={setActiveTab} onSelectCustomer={setSelectedCustomerId} />;
      case 'copilot':
        return <CopilotView />;
      case 'data-sources':
        return <DataSourcesView />;
      case 'catalog':
        return <CatalogView />;
      case 'metrics':
        return <MetricsView />;
      case 'exceptions':
        return <ExceptionsView onSelectCustomer={setSelectedCustomerId} />;
      case 'actions':
        return <ActionCenterView />;
      case 'workflows':
        return <WorkflowView />;
      case 'knowledge':
        return <KnowledgeBaseView />;
      case 'reports':
        return <ReportsView />;
      case 'audit':
        return <AuditView />;
      default:
        return <DashboardView onNavigate={setActiveTab} onSelectCustomer={setSelectedCustomerId} />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex">
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        openExceptionsCount={openExceptionsCount}
        proposedActionsCount={proposedActionsCount}
      />

      {/* Main Container */}
      <div className="flex-1 ml-64 flex flex-col min-h-screen">
        {/* Top Header */}
        <Header
          workspaceName="Acme Industrial Supplies"
          dataHealthScore={91.6}
          onRunMorningReview={handleRunMorningReview}
          onLoadDemo={handleLoadDemo}
          onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
          isLoadingDemo={isLoadingDemo}
          isRunningReview={isRunningReview}
        />

        {/* Dynamic View Content */}
        <main className="flex-1 p-8 mt-16 overflow-y-auto">
          {renderActiveView()}
        </main>
      </div>

      {/* Morning Operations Review Modal */}
      <MorningReviewModal
        isOpen={isMorningReviewOpen}
        onClose={() => setIsMorningReviewOpen(false)}
        data={morningReviewData}
        onNavigateToActions={() => setActiveTab('actions')}
      />

      {/* Command Palette Modal (Ctrl + K) */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        onNavigate={setActiveTab}
        onAskCopilot={(q) => {
          setActiveTab('copilot');
        }}
        onRunMorningReview={handleRunMorningReview}
      />

      {/* Customer 360 Drilldown Modal */}
      <Customer360Modal
        customerId={selectedCustomerId}
        onClose={() => setSelectedCustomerId(null)}
      />
    </div>
  );
}

export default App;
