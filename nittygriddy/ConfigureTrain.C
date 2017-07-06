#include <string>

#include <TROOT.h>
#include <AliPhysicsSelectionTask.h>

void ConfigureTrain() {
  // Add mult selection Task
  gROOT->LoadMacro("$ALICE_PHYSICS/OADB/COMMON/MULTIPLICITY/macros/AddTaskMultSelection.C");
  gROOT->ProcessLine("AddTaskMultSelection()");

  // PhysicsSelection Configuration
  gROOT->LoadMacro("$ALICE_PHYSICS/OADB/macros/AddTaskPhysicsSelection.C");
  // Use a reinterpreted cast to get the task for further configurations in this task
  AliPhysicsSelectionTask* ps = reinterpret_cast<AliPhysicsSelectionTask*>
    // Signature: Bool_t mCAnalysisFlag, Bool_t applyPileupCuts
    (gROOT->ProcessLine("AddTaskPhysicsSelection(false, true)"));

  // Add you own task here...
}
