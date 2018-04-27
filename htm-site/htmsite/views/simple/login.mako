<%inherit file="layout.mako"/>
<form action="${url}" method="post" class="form-signin">
    <input type="hidden" name="came_from" value="${came_from}"/>
    <h2 class="form-signin-heading">Please sign in</h2>
    <label for="inputEmail" class="sr-only">Email address</label>
    <input id="email" name="username" class="form-control" value="${username}" placeholder="Username"
           required autofocus>
    <label for="inputPassword" class="sr-only">Password</label>
    <input type="password" id="password" name="password" class="form-control" value="${password}"
           placeholder="Password" required>
    <div class="checkbox">
        <label>
            <input type="checkbox" value="remember-me"> Remember me
        </label>
    </div>
    %if message:
        <div id="submit-message" class="alert alert-danger" role="alert">${message}</div>
    %endif

    <button class="btn btn-lg btn-primary btn-block" name="form.submitted" type="submit">Sign in</button>
</form>