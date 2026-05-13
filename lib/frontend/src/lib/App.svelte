<script lang="ts">
  import "$lib/app.css";
  import { Router, Route } from 'svelte-routing';
  import Header from "$components/ui/Header.svelte";
  import Middle from "$components/ui/Middle.svelte";
  import Footer from "$components/ui/Footer.svelte";
  import RecordViewer from "$components/ui/Record/RecordViewer.svelte";
  import { filters } from "$states/index";

  let isRecordViewer = $state(false);
  let recordViewerTitle = $state("");
</script>

<Router>
  <!-- Background gradient and main container -->
  <div
    class="min-h-screen bg-linear-to-br from-[#052b1c] to-[#55b949] flex flex-col p-0"
  >
    <!-- Top header at very top, full width, reactive properties -->
    <Header
      isRelatedMode={filters.isRelatedMode}
      {isRecordViewer}
      {recordViewerTitle}
    />
 
    <!-- Main content area with routing -->
    <div style="margin-top:76px;">
      <Route path="/">
        {(() => {
          isRecordViewer = false;
          return '';
        })()}
        <Middle/>
      </Route>
      <!-- params is a special variable that contains the URL parameters -->
      <Route path="/:endpoint/:id" let:params>
        {(() => {
          isRecordViewer = true;
          return '';
        })()}
        <RecordViewer
          endpointKey={params.endpoint}
          recordId={params.id}
          onRecordLoaded={(title: string) => recordViewerTitle = title}
        />
      </Route>
    </div>
 
    <Footer />
  </div>
</Router>
