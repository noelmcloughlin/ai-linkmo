<script lang="ts">
  import '$lib/app.css';
  import { Router, Route } from 'svelte-routing';
  import Header from '$components/ui/Header.svelte';
  import Middle from '$components/ui/Middle.svelte';
  import Footer from '$components/ui/Footer.svelte';
  import RecordViewer from '$components/ui/Record/RecordViewer.svelte';
  import { filters } from '$states/index';
  import { HEADER_HEIGHT } from '$lib/constants';

  let isRecordViewer = $state(false);
  let recordViewerTitle = $state('');

  // Scroll to top on route change for better UX (browser stores prior scroll
  // position by default; with client-side routing that is rarely desirable).
  function scrollTop() {
    if (typeof window !== 'undefined') {
      window.scrollTo({ top: 0, behavior: 'instant' });
    }
  }
</script>

<Router>
  <!-- Background gradient and main container -->
  <div class="flex min-h-screen flex-col bg-linear-to-br from-[#052b1c] to-[#55b949] p-0">
    <!-- Top header at very top, full width, reactive properties -->
    <Header isRelatedMode={filters.isRelatedMode} {isRecordViewer} {recordViewerTitle} />

    <!-- Main content area with routing -->
    <div style="margin-top: calc({HEADER_HEIGHT} - 1.5rem);">
      <Route path="/">
        <Middle
          onMounted={() => {
            isRecordViewer = false;
            recordViewerTitle = '';
            scrollTop();
          }}
        />
      </Route>
      <!-- params is a special variable that contains the URL parameters -->
      <Route path="/:endpoint/:id" let:params>
        <RecordViewer
          endpointKey={params.endpoint}
          recordId={params.id}
          onRecordLoaded={(title: string) => {
            isRecordViewer = true;
            recordViewerTitle = title;
            scrollTop();
          }}
        />
      </Route>
    </div>

    <Footer />
  </div>
</Router>
