<%@ page contentType="text/html;charset=UTF-8" pageEncoding="UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Scriptorium &mdash; Legacy Admin &middot; Corpus</title>
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
  <nav aria-label="breadcrumb">
    <ol class="breadcrumb">
      <li class="breadcrumb-item"><a href="/legacy/admin/">Tenants</a></li>
      <li class="breadcrumb-item active" aria-current="page">Corpus</li>
    </ol>
  </nav>

  <h1 class="h4">Corpus for tenant <code><c:out value="${tenantId}"/></code></h1>
  <p class="text-muted">
    Knowledge graph: <c:out value="${graphStats.entityCount()}"/> entities,
    <c:out value="${graphStats.relationCount()}"/> relations.
  </p>

  <div class="row mb-3">
    <div class="col-12 col-md-6">
      <label class="form-label" for="doc-filter">Filter documents</label>
      <input type="search" class="form-control" id="doc-filter"
             placeholder="Type to filter by id or preview&hellip;">
    </div>
  </div>

  <div class="table-responsive">
    <table class="table table-striped bg-white" id="documents-table">
      <caption class="text-muted small">
        Indexed documents in this tenant's OpenSearch index (first-chunk preview).
      </caption>
      <thead>
        <tr>
          <th scope="col">Document</th>
          <th scope="col" class="text-end">Chunks</th>
          <th scope="col">Preview</th>
        </tr>
      </thead>
      <tbody>
        <c:forEach items="${documents}" var="d">
          <tr>
            <td><code><c:out value="${d.documentId()}"/></code></td>
            <td class="text-end"><c:out value="${d.chunkCount()}"/></td>
            <td class="small"><c:out value="${d.preview()}"/></td>
          </tr>
        </c:forEach>
        <c:if test="${empty documents}">
          <tr><td colspan="3" class="text-muted">Nothing indexed for this tenant yet.</td></tr>
        </c:if>
      </tbody>
    </table>
  </div>
</main>
<script src="/webjars/jquery/3.7.1/jquery.min.js"></script>
<script src="/webjars/bootstrap/5.3.7/js/bootstrap.bundle.min.js"></script>
<script>
  // Classic jQuery client-side table filter.
  $(function () {
    $('#doc-filter').on('input', function () {
      var needle = $(this).val().toLowerCase();
      $('#documents-table tbody tr').each(function () {
        var $row = $(this);
        $row.toggle($row.text().toLowerCase().indexOf(needle) !== -1);
      });
    });
  });
</script>
</body>
</html>
