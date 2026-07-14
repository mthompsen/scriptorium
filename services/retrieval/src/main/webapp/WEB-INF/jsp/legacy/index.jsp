<%@ page contentType="text/html;charset=UTF-8" pageEncoding="UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Scriptorium &mdash; Legacy Admin Console</title>
  <link rel="stylesheet" href="/webjars/bootstrap/5.3.7/css/bootstrap.min.css">
</head>
<body class="bg-light">
<nav class="navbar navbar-dark bg-dark">
  <div class="container">
    <span class="navbar-brand">Scriptorium &middot; Legacy Admin Console</span>
    <span class="navbar-text d-none d-md-inline">JSP + jQuery + Bootstrap</span>
  </div>
</nav>
<main class="container py-4">
  <div class="alert alert-warning" role="alert">
    <strong>Legacy surface.</strong> This console is served server-side (JSP) by the
    retrieval service and is integrated deliberately as a mixed-technology exercise
    (ARCHITECTURE.md &sect;10). The modern admin UI lives in the Next.js app.
  </div>

  <div class="d-flex justify-content-between align-items-center mb-3">
    <h1 class="h4 mb-0">Tenant corpora</h1>
    <button id="refresh" type="button" class="btn btn-primary btn-sm">Refresh</button>
  </div>

  <div class="table-responsive">
    <table class="table table-striped table-hover bg-white" id="tenants-table">
      <caption class="text-muted small">
        Chunk counts from OpenSearch; entity/relation counts from Neo4j.
      </caption>
      <thead>
        <tr>
          <th scope="col">Tenant</th>
          <th scope="col" class="text-end">Chunks</th>
          <th scope="col" class="text-end">Entities</th>
          <th scope="col" class="text-end">Relations</th>
          <th scope="col"></th>
        </tr>
      </thead>
      <tbody>
        <c:forEach items="${tenants}" var="t">
          <tr>
            <td><code><c:out value="${t.tenantId()}"/></code></td>
            <td class="text-end"><c:out value="${t.chunkCount()}"/></td>
            <td class="text-end"><c:out value="${t.entityCount()}"/></td>
            <td class="text-end"><c:out value="${t.relationCount()}"/></td>
            <td class="text-end">
              <a class="btn btn-outline-secondary btn-sm"
                 href="/legacy/admin/corpus?tenant_id=<c:out value="${t.tenantId()}"/>">View corpus</a>
            </td>
          </tr>
        </c:forEach>
        <c:if test="${empty tenants}">
          <tr><td colspan="5" class="text-muted">No tenant has indexed any documents yet.</td></tr>
        </c:if>
      </tbody>
    </table>
  </div>
</main>
<script src="/webjars/jquery/3.7.1/jquery.min.js"></script>
<script src="/webjars/bootstrap/5.3.7/js/bootstrap.bundle.min.js"></script>
<script>
  // In-page refresh against the console's JSON API. Rows are built with
  // DOM/text() calls, never HTML string concatenation, so values stay escaped.
  $(function () {
    $('#refresh').on('click', function () {
      var $btn = $(this).prop('disabled', true);
      $.getJSON('/legacy/admin/api/tenants')
        .done(function (tenants) {
          var $tbody = $('#tenants-table tbody').empty();
          if (tenants.length === 0) {
            $tbody.append($('<tr>').append(
              $('<td>').attr('colspan', 5).addClass('text-muted')
                .text('No tenant has indexed any documents yet.')));
            return;
          }
          $.each(tenants, function (_, t) {
            var link = $('<a>').addClass('btn btn-outline-secondary btn-sm')
              .attr('href', '/legacy/admin/corpus?tenant_id=' + encodeURIComponent(t.tenant_id))
              .text('View corpus');
            $tbody.append($('<tr>')
              .append($('<td>').append($('<code>').text(t.tenant_id)))
              .append($('<td>').addClass('text-end').text(t.chunk_count))
              .append($('<td>').addClass('text-end').text(t.entity_count))
              .append($('<td>').addClass('text-end').text(t.relation_count))
              .append($('<td>').addClass('text-end').append(link)));
          });
        })
        .always(function () { $btn.prop('disabled', false); });
    });
  });
</script>
</body>
</html>
